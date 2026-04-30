"""FastAPI app for the local Commonplace web UI."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markdown import markdown
import yaml

from .. import cli
from ..config import COMMONPLACE_CONFIG
from ..propose import _collect_escalation_triggers

UI_HOST = "127.0.0.1"
UI_PORT = 8765
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_UPLOAD_SUFFIXES = {".md", ".pdf"}
UI_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(UI_DIR / "templates"))
SOURCES_DIR = cli.REPO_ROOT / "sources" / "incoming"


def create_app() -> FastAPI:
    """Create the local-only FastAPI application."""
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        items = list_inbox_items()
        selected = load_inbox_detail(items[0]["filename"]) if items else None
        return TEMPLATES.TemplateResponse(
            request,
            "index.html",
            {
                "items": items,
                "selected": selected,
                "inbox_count": len(items),
                "last_sync_time": get_last_sync_time(),
                "ui_host": UI_HOST,
                "ui_port": UI_PORT,
            },
        )

    @app.get("/inbox")
    def inbox_items() -> dict[str, object]:
        items = list_inbox_items()
        return {
            "items": items,
            "inbox_count": len(items),
            "last_sync_time": get_last_sync_time(),
        }

    @app.get("/inbox/{filename}")
    def inbox_detail(filename: str) -> dict[str, object]:
        return load_inbox_detail(filename)

    @app.get("/book/entries")
    def book_entries() -> dict[str, object]:
        return {"entries": list_book_entries()}

    @app.put("/inbox/{filename}")
    async def update_inbox_proposal(filename: str, request: Request) -> dict[str, object]:
        try:
            payload = await request.json()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="Invalid JSON payload.") from exc
        return update_inbox_proposal_file(filename, payload)

    @app.post("/inbox/{filename}/promote")
    async def promote_proposal(filename: str, request: Request) -> dict[str, object]:
        payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        copy_file = bool(payload.get("copy", False))
        try:
            destination = cli.run_promote(
                path=filename,
                latest=False,
                copy_file=copy_file,
                assume_yes=True,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "promoted_to": str(destination),
            "copy": copy_file,
            "inbox_count": len(list_inbox_items()),
        }

    @app.post("/inbox/{filename}/discard")
    def discard_proposal(filename: str) -> dict[str, str]:
        source_path = cli._resolve_inbox_markdown_path(filename)
        archived_path = archive_inbox_file(source_path)
        return {"archived_to": str(archived_path)}

    @app.post("/sync-book")
    def sync_book() -> dict[str, object]:
        index_path, topics_path = cli.run_sync_book(assume_yes=True)
        return {
            "index_path": str(index_path),
            "topics_path": str(topics_path),
            "inbox_count": len(list_inbox_items()),
            "last_sync_time": get_last_sync_time(),
        }

    @app.post("/ingest")
    async def ingest_files(files: list[UploadFile] = File(...)) -> dict[str, object]:
        results: list[dict[str, object]] = []
        incoming_dir = SOURCES_DIR / datetime.now().date().isoformat()
        incoming_dir.mkdir(parents=True, exist_ok=True)

        for upload in files:
            result = {
                "original_name": upload.filename or "",
                "saved_source_path": None,
                "inbox_filename": None,
                "error": None,
            }
            try:
                suffix = Path(upload.filename or "").suffix.lower()
                if suffix not in ALLOWED_UPLOAD_SUFFIXES:
                    raise ValueError(f"Unsupported upload type: {suffix or '<none>'}")

                file_bytes = await upload.read()
                if len(file_bytes) > MAX_UPLOAD_BYTES:
                    raise ValueError(
                        f"File exceeds 25 MB limit: {upload.filename}"
                    )

                saved_path = incoming_dir / Path(upload.filename or "upload").name
                saved_path.write_bytes(file_bytes)
                result["saved_source_path"] = str(saved_path)

                inbox_path = cli.run_ingest(path=str(saved_path))
                ensure_source_path_frontmatter(inbox_path, str(saved_path))
                result["inbox_filename"] = inbox_path.name
            except Exception as exc:  # noqa: BLE001
                result["error"] = str(exc)
            results.append(result)

        return {
            "results": results,
            "inbox_count": len(list_inbox_items()),
            "last_sync_time": get_last_sync_time(),
        }

    return app


def list_inbox_items() -> list[dict[str, object]]:
    """Return inbox proposal summaries newest first."""
    items: list[dict[str, object]] = []
    for path in cli.list_inbox_markdown_files():
        detail = load_inbox_detail(path.name)
        items.append(
            {
                "filename": detail["filename"],
                "title": detail["proposal"]["title"],
                "action": detail["proposal"]["action"],
                "confidence": detail["proposal"]["confidence"],
                "needs_escalation": detail["proposal"]["needs_escalation"],
                "escalation_triggers": detail["proposal"]["escalation_triggers"],
            }
        )
    return items


def load_inbox_detail(filename: str) -> dict[str, object]:
    """Load a structured view of one inbox proposal file."""
    path = cli._resolve_inbox_markdown_path(filename)
    text = path.read_text(encoding="utf-8")
    front_matter, body_markdown = split_front_matter(text)
    parsed = yaml.safe_load(front_matter) or {}
    proposal_data = parsed.get("proposal", {})
    source_data = make_json_safe(parsed.get("source", {}))
    proposal_view = normalize_proposal_view(path, proposal_data)
    resolved_target = None
    if proposal_view["action"] == "append-to" and proposal_view["target_entry"]:
        try:
            resolved_target = str(
                cli._resolve_book_destination(
                    cli.ReviewedProposal(
                        source_path=path,
                        action=proposal_view["action"],
                        target_entry=proposal_view["target_entry"],
                        body=body_markdown,
                    )
                )
            )
        except FileNotFoundError:
            resolved_target = None

    return {
        "filename": path.name,
        "path": str(path),
        "proposal": proposal_view,
        "source": source_data,
        "body_markdown": body_markdown,
        "body_html": markdown(body_markdown),
        "resolved_target_entry_path": resolved_target,
    }


def normalize_proposal_view(path: Path, proposal_data: dict[str, object]) -> dict[str, object]:
    """Normalize front-matter proposal data for UI use."""
    title = str(proposal_data.get("title") or extract_first_heading(path.read_text(encoding="utf-8")) or path.stem)
    topics = [str(topic) for topic in proposal_data.get("topics", [])]
    proposal_like = SimpleNamespace(
        action=str(proposal_data.get("action", "")),
        target_entry=proposal_data.get("target_entry"),
        draft_topics=topics,
        confidence=str(proposal_data.get("confidence", "")),
        needs_escalation=bool(proposal_data.get("needs_escalation", False)),
    )
    triggers = _collect_escalation_triggers(proposal_like)
    return {
        "title": title,
        "action": str(proposal_data.get("action", "")),
        "target_entry": proposal_data.get("target_entry"),
        "kind": str(proposal_data.get("kind", "")),
        "topics": topics,
        "why_kept": str(proposal_data.get("why_kept", "")),
        "reasoning": str(proposal_data.get("reasoning", "")),
        "confidence": str(proposal_data.get("confidence", "")),
        "needs_escalation": bool(proposal_data.get("needs_escalation", False)),
        "last_edited_at": stringify_datetime(proposal_data.get("last_edited_at")),
        "escalation_triggers": triggers,
    }


def list_book_entries() -> list[dict[str, object]]:
    """Return canonical book entries for UI selection."""
    return [
        {
            "filename": entry.path.name,
            "title": entry.title,
            "kind": entry.kind,
            "topics": entry.topics,
        }
        for entry in cli.load_book_entries()
    ]


def update_inbox_proposal_file(filename: str, payload: dict[str, object]) -> dict[str, object]:
    """Update editable inbox proposal fields and persist atomically."""
    allowed_fields = {"title", "kind", "topics", "why_kept", "action", "target_entry", "body"}
    unknown_fields = sorted(set(payload) - allowed_fields)
    if unknown_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown editable fields: {', '.join(unknown_fields)}",
        )

    path = cli._resolve_inbox_markdown_path(filename)
    text = path.read_text(encoding="utf-8")
    front_matter, body_markdown = split_front_matter(text)
    parsed = yaml.safe_load(front_matter) or {}
    proposal = parsed.setdefault("proposal", {})
    source = parsed.setdefault("source", {})

    action = str(payload.get("action", proposal.get("action", "")))
    if action not in {"new-entry", "append-to", "flag-for-judgment"}:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    title = str(payload.get("title", proposal.get("title", ""))).strip()
    kind = str(payload.get("kind", proposal.get("kind", ""))).strip()
    why_kept = str(payload.get("why_kept", proposal.get("why_kept", ""))).strip()
    body = str(payload.get("body", body_markdown)).rstrip()
    topics = normalize_topics_input(payload.get("topics", proposal.get("topics", [])))
    target_entry = payload.get("target_entry")
    target_entry = str(target_entry).strip() if target_entry is not None else None
    if target_entry == "":
        target_entry = None

    if action == "append-to":
        if not target_entry:
            raise HTTPException(
                status_code=400,
                detail="append-to proposals require a valid target_entry.",
            )
        if not any(entry["title"] == target_entry for entry in list_book_entries()):
            raise HTTPException(
                status_code=400,
                detail=f"Unknown target_entry: {target_entry}",
            )
    else:
        target_entry = None

    proposal["title"] = title
    proposal["kind"] = kind
    proposal["topics"] = topics
    proposal["why_kept"] = why_kept
    proposal["action"] = action
    proposal["target_entry"] = target_entry
    proposal["last_edited_at"] = datetime.now().astimezone().isoformat()

    if "confidence" not in proposal:
        proposal["confidence"] = ""
    if "needs_escalation" not in proposal:
        proposal["needs_escalation"] = False
    source.setdefault("source_path", source.get("source_path"))

    rewritten = (
        f"---\n"
        f"{yaml.safe_dump(parsed, sort_keys=False, allow_unicode=True).rstrip()}\n"
        f"---\n\n{body}\n"
    )
    atomic_write_text(path, rewritten)
    return load_inbox_detail(filename)


def split_front_matter(text: str) -> tuple[str, str]:
    """Split YAML front-matter from markdown body."""
    if not text.startswith("---\n"):
        raise HTTPException(status_code=400, detail="Proposal file is missing front-matter.")
    closing_marker = text.find("\n---\n", 4)
    if closing_marker == -1:
        raise HTTPException(status_code=400, detail="Proposal file has malformed front-matter.")
    front_matter = text[4:closing_marker]
    body = text[closing_marker + len("\n---\n") :].lstrip("\n")
    return front_matter, body


def extract_first_heading(text: str) -> str | None:
    """Extract the first markdown heading as a fallback title."""
    _, body = split_front_matter(text)
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return None


def archive_inbox_file(path: Path) -> Path:
    """Move an inbox file into a dated archive folder."""
    archive_dir = cli.INBOX_DIR / "_archive" / datetime.now().date().isoformat()
    archive_dir.mkdir(parents=True, exist_ok=True)
    destination = archive_dir / path.name
    if destination.exists():
        stem = destination.stem
        suffix = destination.suffix
        counter = 2
        while True:
            candidate = archive_dir / f"{stem}-{counter}{suffix}"
            if not candidate.exists():
                destination = candidate
                break
            counter += 1
    shutil.move(str(path), str(destination))
    return destination


def get_last_sync_time() -> str | None:
    """Return the last sync time inferred from book index/topic file mtimes."""
    sync_targets = [cli.BOOK_DIR / "_index.md", cli.BOOK_DIR / "_topics.md"]
    existing = [path for path in sync_targets if path.exists()]
    if not existing:
        return None
    latest = max(path.stat().st_mtime for path in existing)
    return datetime.fromtimestamp(latest).astimezone().isoformat()


def ensure_source_path_frontmatter(path: Path, source_path: str) -> None:
    """Ensure the saved source path is recorded under source.source_path."""
    text = path.read_text(encoding="utf-8")
    front_matter, body = split_front_matter(text)
    parsed = yaml.safe_load(front_matter) or {}
    source = parsed.setdefault("source", {})
    source["source_path"] = source_path
    rewritten = (
        f"---\n"
        f"{yaml.safe_dump(parsed, sort_keys=False, allow_unicode=True).rstrip()}\n"
        f"---\n\n{body.rstrip()}\n"
    )
    atomic_write_text(path, rewritten)


def atomic_write_text(path: Path, text: str) -> None:
    """Write a text file atomically in the same directory."""
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        suffix=path.suffix,
    ) as temp_file:
        temp_file.write(text)
        temp_path = Path(temp_file.name)
    temp_path.replace(path)


def normalize_topics_input(value: object) -> list[str]:
    """Normalize topics from either a list or a comma-delimited string."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def make_json_safe(value: object) -> object:
    """Convert parsed YAML values into JSON-safe primitives for the UI."""
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    return stringify_datetime(value)


def stringify_datetime(value: object) -> object:
    """Render date and datetime values as ISO strings."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value

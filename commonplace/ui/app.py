"""FastAPI app for the local Commonplace web UI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import shutil
import tempfile
from types import SimpleNamespace

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markdown import markdown
from openai import OpenAI
import yaml

from .. import cli
from ..config import COMMONPLACE_CONFIG
from ..propose import _collect_escalation_triggers, _load_openai_api_key

UI_HOST = "127.0.0.1"
UI_PORT = 8765
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_UPLOAD_SUFFIXES = {".md", ".pdf"}
UI_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(UI_DIR / "templates"))
SOURCES_DIR = cli.REPO_ROOT / "sources" / "incoming"
CHAT_MODEL = COMMONPLACE_CONFIG.smart_model
CHAT_SYSTEM_PROMPT = """
You are the librarian of a personal commonplace book.

Treat the supplied commonplace material as primary evidence for how this book
already thinks.

When the question is directly answered by the supplied entries, answer from the
book itself and stay grounded in the provided text.

When the question goes beyond what the book directly covers, say that plainly.
Then still be helpful: offer a clearly labeled inference about what the book
might think next, based on its existing themes, interests, standards, and
patterns. Do not present those inferences as established book content.

Never fabricate supporting evidence or claim the book already contains material
that was not supplied. Keep the line clear between:
- what the book explicitly says
- what you are inferring from the book's existing shape

Synthesize across entries when useful. Quote sparingly. Prefer clear, direct
prose over ornament.
""".strip()

ANNOTATION_QUERY_TERMS = {
    "annotation",
    "annotations",
    "annotated",
    "note",
    "notes",
    "noted",
    "margin",
    "marginalia",
    "highlight",
    "highlights",
    "pov",
    "point",
    "view",
    "perspective",
    "reaction",
    "reactions",
    "take",
    "takes",
}


@dataclass(frozen=True)
class ChatBookEntry:
    """Canonical book entry metadata used for metadata-first routing."""

    path: Path
    title: str
    kind: str
    why_kept: str
    topics: list[str]
    related_entries: list[str]
    annotations: list[str]
    body: str | None = None


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

    @app.get("/book/{filename}")
    def book_entry_detail(filename: str) -> dict[str, object]:
        return load_book_detail(filename)

    @app.put("/book/{filename}/annotations")
    async def update_book_entry_annotations(filename: str, request: Request) -> dict[str, object]:
        try:
            payload = await request.json()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="Invalid JSON payload.") from exc
        return update_book_annotations(filename, payload)

    @app.post("/chat")
    async def chat_query(request: Request) -> dict[str, object]:
        try:
            payload = await request.json()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="Invalid JSON payload.") from exc

        query = str(payload.get("query", "")).strip()
        if not query:
            raise HTTPException(status_code=400, detail="A query is required.")

        try:
            return answer_commonplace_query(query=query)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

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
        try:
            index_path, topics_path = cli.run_sync_book(assume_yes=True)
        except (RuntimeError, ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
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
        "body_html": render_markdown_html(body_markdown),
        "resolved_target_entry_path": resolved_target,
    }


def load_book_detail(filename: str) -> dict[str, object]:
    """Load one canonical book entry for Reading Room detail display."""
    path = resolve_book_entry_path(filename)

    text = path.read_text(encoding="utf-8")
    front_matter, body_markdown = split_book_front_matter(text, path)
    metadata = make_json_safe(yaml.safe_load(front_matter) or {})

    title = str(metadata.get("title", path.stem))
    kind = str(metadata.get("kind", ""))
    why_kept = str(metadata.get("why-kept", ""))
    topics = normalize_topics_input(metadata.get("topics", []))
    related_entries = normalize_topics_input(metadata.get("related-entries", []))
    annotations = normalize_topics_input(metadata.get("annotations", []))

    return {
        "filename": path.name,
        "path": str(path),
        "entry": {
            "title": title,
            "kind": kind,
            "why_kept": why_kept,
            "topics": topics,
            "related_entries": related_entries,
            "annotations": annotations,
        },
        "body_markdown": body_markdown,
        "body_html": render_markdown_html(body_markdown),
    }


def resolve_book_entry_path(filename: str) -> Path:
    """Resolve a canonical book entry by exact filename."""
    normalized = Path(filename).name
    for path in cli.BOOK_DIR.glob("*.md"):
        if path.name in cli.BOOK_SCAFFOLD_FILES:
            continue
        if path.name == normalized:
            return path
    raise HTTPException(status_code=404, detail=f"Unknown book entry: {filename}")


def update_book_annotations(filename: str, payload: dict[str, object]) -> dict[str, object]:
    """Update the annotation list for one canonical book entry."""
    if set(payload) - {"annotations"}:
        unknown_fields = ", ".join(sorted(set(payload) - {"annotations"}))
        raise HTTPException(status_code=400, detail=f"Unknown editable fields: {unknown_fields}")

    path = resolve_book_entry_path(filename)
    text = path.read_text(encoding="utf-8")
    front_matter, body = split_book_front_matter(text, path)
    parsed = yaml.safe_load(front_matter) or {}
    parsed["annotations"] = normalize_annotation_input(payload.get("annotations", parsed.get("annotations", [])))

    rewritten = (
        f"---\n"
        f"{yaml.safe_dump(parsed, sort_keys=False, allow_unicode=True).rstrip()}\n"
        f"---\n\n{body.rstrip()}\n"
    )
    atomic_write_text(path, rewritten)
    return load_book_detail(filename)


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
        "annotation": str(proposal_data.get("annotation", "")),
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


def load_chat_book_entries(book_dir: Path | None = None) -> list[ChatBookEntry]:
    """Load canonical book entries with metadata-first routing fields."""
    active_book_dir = book_dir or cli.BOOK_DIR
    entries: list[ChatBookEntry] = []
    for path in sorted(active_book_dir.glob("*.md")):
        if path.name in cli.BOOK_SCAFFOLD_FILES:
            continue
        entries.append(parse_chat_book_entry(path))
    return entries


def parse_chat_book_entry(path: Path) -> ChatBookEntry:
    """Parse one canonical book entry for chat routing and stuffing."""
    metadata = yaml.safe_load(read_book_front_matter(path)) or {}

    title = str(metadata.get("title", "")).strip()
    kind = str(metadata.get("kind", "")).strip()
    why_kept = str(metadata.get("why-kept", "")).strip()
    topics = normalize_topics_input(metadata.get("topics", []))
    related_entries = normalize_topics_input(metadata.get("related-entries", []))
    annotations = normalize_topics_input(metadata.get("annotations", []))

    if not title or not kind or not why_kept:
        raise ValueError(f"Book entry is missing required metadata: {path}")

    return ChatBookEntry(
        path=path,
        title=title,
        kind=kind,
        why_kept=why_kept,
        topics=topics,
        related_entries=related_entries,
        annotations=annotations,
        body=None,
    )


def answer_commonplace_query(query: str, client: OpenAI | None = None) -> dict[str, object]:
    """Answer a user query by routing over metadata, then stuffing only matched entries."""
    entries = load_chat_book_entries()
    matched_entries = route_query_to_entries(query=query, entries=entries)
    prompt_entries = matched_entries
    prompt_mode = "matched-entries"
    if not matched_entries:
        prompt_entries = summarize_book_catalog(entries)
        prompt_mode = "catalog-inference"

    active_client = client or OpenAI(api_key=_load_openai_api_key())
    prompt = build_chat_prompt(
        query=query,
        entries=prompt_entries,
        mode=prompt_mode,
        emphasize_annotations=query_requests_annotations(query),
    )
    answer = request_chat_answer(
        client=active_client,
        query=query,
        prompt=prompt,
        model=CHAT_MODEL,
    )
    return {
        "answer": answer,
        "answer_html": render_markdown_html(answer),
        "matched_entries": [
            {
                "filename": entry.path.name,
                "title": entry.title,
                "kind": entry.kind,
                "topics": entry.topics,
                "related_entries": entry.related_entries,
                "annotations": entry.annotations,
            }
            for entry in matched_entries
        ],
        "model": CHAT_MODEL,
    }


def route_query_to_entries(query: str, entries: list[ChatBookEntry], limit: int = 3) -> list[ChatBookEntry]:
    """Route a query using entry metadata only, then expand through explicit relations."""
    query_lower = query.lower()
    query_tokens = tokenize_metadata_text(query)
    if not query_tokens:
        return []

    scored: list[tuple[int, ChatBookEntry]] = []
    for entry in entries:
        title_tokens = tokenize_metadata_text(entry.title)
        topic_tokens = {token for topic in entry.topics for token in tokenize_metadata_text(topic)}
        kind_tokens = tokenize_metadata_text(entry.kind)
        related_tokens = {
            token
            for related_entry in entry.related_entries
            for token in tokenize_metadata_text(related_entry)
        }
        why_tokens = tokenize_metadata_text(entry.why_kept)
        annotation_tokens = {
            token
            for annotation in entry.annotations
            for token in tokenize_metadata_text(annotation)
        }
        score = 0
        if entry.title.lower() in query_lower or query_lower in entry.title.lower():
            score += 14
        score += 4 * len(query_tokens & title_tokens)
        score += 6 * len(query_tokens & topic_tokens)
        score += 3 * len(query_tokens & kind_tokens)
        score += 2 * len(query_tokens & related_tokens)
        score += len(query_tokens & why_tokens)
        score += 2 * len(query_tokens & annotation_tokens)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda item: (-item[0], item[1].title.lower()))
    primary = [entry for _, entry in scored[:limit]]
    if not primary:
        return []

    title_map = {entry.title: entry for entry in entries}
    expanded: list[ChatBookEntry] = []
    seen_titles: set[str] = set()
    for entry in primary:
        if entry.title not in seen_titles:
            expanded.append(entry)
            seen_titles.add(entry.title)
        for related_title in entry.related_entries:
            related_entry = title_map.get(related_title)
            if related_entry and related_entry.title not in seen_titles:
                expanded.append(related_entry)
                seen_titles.add(related_entry.title)

    return [load_chat_entry_body(entry) for entry in expanded[:limit]]


def load_chat_entry_body(entry: ChatBookEntry) -> ChatBookEntry:
    """Load the full markdown body only after routing has selected an entry."""
    text = entry.path.read_text(encoding="utf-8")
    _, body = split_book_front_matter(text, entry.path)
    return ChatBookEntry(
        path=entry.path,
        title=entry.title,
        kind=entry.kind,
        why_kept=entry.why_kept,
        topics=entry.topics,
        related_entries=entry.related_entries,
        annotations=entry.annotations,
        body=body.rstrip(),
    )


def summarize_book_catalog(entries: list[ChatBookEntry], limit: int = 12) -> list[ChatBookEntry]:
    """Build a compact metadata-only snapshot for book-voice inference."""
    ranked = sorted(
        entries,
        key=lambda entry: (
            -(len(entry.related_entries) + len(entry.topics) + len(entry.annotations)),
            entry.title.lower(),
        ),
    )
    return ranked[:limit]


def tokenize_metadata_text(text: str) -> set[str]:
    """Tokenize metadata text into a simple lowercase lexical set."""
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 1}


def query_requests_annotations(query: str) -> bool:
    """Return whether the user is explicitly asking about notes or annotations."""
    tokens = tokenize_metadata_text(query)
    if not tokens:
        return False
    if "point" in tokens and "view" in tokens:
        return True
    return any(term in tokens for term in ANNOTATION_QUERY_TERMS)


def build_annotation_pov_context(entries: list[ChatBookEntry]) -> str:
    """Compile a short user point-of-view window from entry annotations."""
    annotation_lines: list[str] = []
    for entry in entries:
        if not entry.annotations:
            continue
        notes = " | ".join(entry.annotations)
        annotation_lines.append(f"- {entry.title}: {notes}")

    if not annotation_lines:
        return (
            "User point-of-view from annotations:\n"
            "(No explicit annotations were supplied for these entries. Fall back to why-kept, topics, and related entries.)"
        )

    return (
        "User point-of-view from annotations:\n"
        "Treat these notes as the clearest available signal of the user's interpretation, emphasis, and taste.\n"
        + "\n".join(annotation_lines)
    )


def build_chat_prompt(
    query: str,
    entries: list[ChatBookEntry],
    mode: str = "matched-entries",
    emphasize_annotations: bool = False,
) -> str:
    """Build the bounded chat prompt for direct answers or book-voice inference."""
    entry_blocks: list[str] = []
    for entry in entries:
        metadata_lines = [
            f"Title: {entry.title}",
            f"Kind: {entry.kind}",
            f"Topics: {', '.join(entry.topics) if entry.topics else '(none)'}",
            f"Related entries: {', '.join(entry.related_entries) if entry.related_entries else '(none)'}",
            f"Annotations: {' | '.join(entry.annotations) if entry.annotations else '(none)'}",
            f"Why kept: {entry.why_kept}",
            "",
            "Content:",
            entry.body or "",
        ]
        entry_blocks.append("\n".join(metadata_lines).strip())

    if mode == "catalog-inference":
        framing = (
            "The book does not appear to contain a directly matched entry for this question.\n"
            "Use the catalog snapshot below to infer how the book might approach the topic.\n"
            "In your answer, first say that the book does not directly address it, then offer a"
            " clearly labeled inference grounded in the book's existing themes."
        )
        section_label = "Commonplace catalog snapshot:"
    else:
        framing = (
            "Use the matched entries below as the main evidence.\n"
            "If they only partially answer the question, say that plainly and then offer a"
            " clearly labeled inference about how the book might extend the thought."
        )
        section_label = "Matched commonplace entries:"

    annotation_context = ""
    if emphasize_annotations:
        annotation_context = (
            "\n\nThe user is explicitly asking about notes, annotations, or point of view.\n"
            "Prioritize the annotation context below when describing the user's perspective,"
            " while still keeping it tied to the supplied entries.\n\n"
            f"{build_annotation_pov_context(entries)}"
        )

    return (
        f"User question:\n{query.strip()}\n\n"
        f"{framing}\n\n"
        f"{annotation_context}"
        f"{'' if not annotation_context else '\n\n'}"
        f"{section_label}\n\n"
        + "\n\n---\n\n".join(entry_blocks)
    ).strip()


def request_chat_answer(client: OpenAI, query: str, prompt: str, model: str) -> str:
    """Request a text answer over the selected commonplace entries."""
    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Commonplace chat failed for query: {query}") from exc

    answer = extract_response_text(response)
    if not answer:
        raise RuntimeError("Commonplace chat returned no answer text.")
    return answer


def extract_response_text(response: object) -> str:
    """Extract plain assistant text from a Responses API reply."""
    output = getattr(response, "output", [])
    parts: list[str] = []
    for item in output:
        if getattr(item, "type", None) != "message":
            continue
        for content_part in getattr(item, "content", []):
            if getattr(content_part, "type", None) == "output_text":
                text = getattr(content_part, "text", "")
                if text:
                    parts.append(str(text))
    return "\n".join(parts).strip()


def update_inbox_proposal_file(filename: str, payload: dict[str, object]) -> dict[str, object]:
    """Update editable inbox proposal fields and persist atomically."""
    payload = normalize_inbox_payload_keys(payload)
    allowed_fields = {"title", "kind", "topics", "why_kept", "annotation", "action", "target_entry", "body"}
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
    annotation = str(payload.get("annotation", proposal.get("annotation", ""))).strip()
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
    proposal["annotation"] = annotation
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


def normalize_inbox_payload_keys(payload: dict[str, object]) -> dict[str, object]:
    """Normalize client payload keys so minor casing differences do not break saves."""
    normalized: dict[str, object] = {}
    aliases = {
        "whykept": "why_kept",
        "targetentry": "target_entry",
    }
    for key, value in payload.items():
        compact = re.sub(r"[^a-z0-9]+", "", str(key).lower())
        normalized_key = aliases.get(compact, str(key).strip().lower())
        normalized[normalized_key] = value
    return normalized


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


def read_book_front_matter(path: Path) -> str:
    """Read only the top front-matter block from a canonical book entry."""
    with path.open("r", encoding="utf-8") as handle:
        first_line = handle.readline()
        if first_line != "---\n":
            raise ValueError(f"Book entry is missing front-matter: {path}")

        front_matter_lines: list[str] = []
        for line in handle:
            if line == "---\n":
                return "".join(front_matter_lines)
            front_matter_lines.append(line)

    raise ValueError(f"Book entry has malformed front-matter: {path}")


def split_book_front_matter(text: str, path: Path) -> tuple[str, str]:
    """Split canonical book front-matter from markdown body."""
    if not text.startswith("---\n"):
        raise ValueError(f"Book entry is missing front-matter: {path}")
    closing_marker = text.find("\n---\n", 4)
    if closing_marker == -1:
        raise ValueError(f"Book entry has malformed front-matter: {path}")
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


def normalize_annotation_input(value: object) -> list[str]:
    """Normalize annotations from either a list or newline-delimited text."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.splitlines() if item.strip()]
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


def render_markdown_html(text: str) -> str:
    """Render markdown into HTML for UI display."""
    return markdown(text, extensions=["extra"])

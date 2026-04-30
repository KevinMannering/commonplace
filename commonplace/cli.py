"""Command-line interface for the Commonplace ingestion workflow."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import textwrap
import shutil
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path

from .config import COMMONPLACE_CONFIG
from .extract import extract_text
from .propose import BookContext, DEFAULT_PROPOSAL_MODEL, propose_entry
from .render import SourceMetadata, render_inbox_markdown, suggest_inbox_filename

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
BOOK_DIR = REPO_ROOT / "book"
INBOX_DIR = REPO_ROOT / "inbox"
BOOK_SCAFFOLD_FILES = {
    ".gitkeep",
    "README.md",
    "CONVENTIONS.md",
    "_index.md",
    "_topics.md",
}
INBOX_SCAFFOLD_FILES = {"README.md"}


@dataclass(frozen=True)
class ReviewedProposal:
    """Minimal parsed representation of a reviewed inbox file."""

    source_path: Path
    action: str
    target_entry: str | None
    body: str


@dataclass(frozen=True)
class BookEntryMetadata:
    """Canonical metadata parsed from a book entry front-matter block."""

    path: Path
    title: str
    kind: str
    why_kept: str
    topics: list[str]


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""
    parser = argparse.ArgumentParser(prog="commonplace")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest a file into the inbox proposal flow.",
    )
    ingest_parser.add_argument("path", help="Path to the source file.")
    ingest_parser.add_argument(
        "-m",
        "--message",
        help="Optional note about why this source matters.",
    )
    ingest_parser.add_argument(
        "--model",
        default=COMMONPLACE_CONFIG.fast_model,
        help="OpenAI model to use for proposal generation.",
    )

    review_parser = subparsers.add_parser(
        "review",
        help="List inbox proposals for human review.",
    )
    review_parser.add_argument(
        "--latest",
        action="store_true",
        help="Show only the newest inbox markdown file.",
    )
    review_parser.add_argument(
        "--open",
        action="store_true",
        help="Open the selected inbox file(s) in the default app.",
    )

    promote_parser = subparsers.add_parser(
        "promote",
        help="Move a reviewed inbox file into the book.",
    )
    promote_target_group = promote_parser.add_mutually_exclusive_group(required=True)
    promote_target_group.add_argument(
        "path",
        nargs="?",
        help="Path to the reviewed inbox markdown file.",
    )
    promote_target_group.add_argument(
        "--latest",
        action="store_true",
        help="Promote the newest inbox markdown file.",
    )
    promote_parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy into the book instead of moving out of the inbox.",
    )
    promote_parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt.",
    )

    sync_parser = subparsers.add_parser(
        "sync-book",
        help="Rebuild book index and topics from canonical entry metadata.",
    )
    sync_parser.add_argument(
        "--yes",
        action="store_true",
        help="Write regenerated files without confirmation.",
    )

    ui_parser = subparsers.add_parser(
        "ui",
        help="Launch the local Commonplace web UI.",
    )
    ui_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface for the local UI server.",
    )
    ui_parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for the local UI server.",
    )

    return parser


def load_book_context(book_dir: Path | None = None) -> BookContext:
    """Load the lightweight book context used by proposal generation."""
    active_book_dir = book_dir or BOOK_DIR
    index_text = (active_book_dir / "_index.md").read_text(encoding="utf-8")
    topics_text = (active_book_dir / "_topics.md").read_text(encoding="utf-8")
    entry_titles = discover_entry_titles(active_book_dir)
    return BookContext(
        index_text=index_text,
        topics_text=topics_text,
        entry_titles=entry_titles,
    )


def discover_entry_titles(book_dir: Path | None = None) -> list[str]:
    """Discover durable book entry titles while excluding scaffold files."""
    active_book_dir = book_dir or BOOK_DIR
    titles: list[str] = []

    for path in sorted(active_book_dir.glob("*.md")):
        if path.name in BOOK_SCAFFOLD_FILES:
            continue
        titles.append(_read_entry_title(path))

    return titles


def run_ingest(
    path: str,
    message: str | None = None,
    model: str = DEFAULT_PROPOSAL_MODEL,
) -> Path:
    """Run the end-to-end ingest flow and write an inbox markdown file."""
    source_path = Path(path).expanduser().resolve()
    extracted = extract_text(source_path)
    book_context = load_book_context()
    proposal = propose_entry(
        source_text=extracted.content_text,
        book_context=book_context,
        message=message,
        model=model,
    )
    ingested_at = datetime.now().astimezone()
    source_metadata = SourceMetadata(
        filename=extracted.filename,
        source_path=str(extracted.path),
        ingested_at=ingested_at,
        message=message,
    )
    markdown = render_inbox_markdown(proposal, source_metadata)

    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    filename = suggest_inbox_filename(
        proposal=proposal,
        for_date=ingested_at.date(),
        fallback_stem=extracted.path.stem,
    )
    output_path = INBOX_DIR / filename
    if output_path.exists():
        raise FileExistsError(f"Inbox file already exists: {output_path}")
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def run_review(latest: bool = False, open_files: bool = False) -> list[Path]:
    """List inbox markdown files newest first and optionally open them."""
    inbox_files = list_inbox_markdown_files()
    selected = inbox_files[:1] if latest else inbox_files

    for path in selected:
        print(path)

    if open_files:
        for path in selected:
            _open_path(path)

    return selected


def run_promote(
    path: str | None = None,
    latest: bool = False,
    copy_file: bool = False,
    assume_yes: bool = False,
) -> Path:
    """Admit a reviewed inbox markdown file into the book under human control."""
    source_path = (
        _resolve_latest_inbox_file() if latest else _resolve_inbox_markdown_path(path)
    )
    reviewed = _read_reviewed_proposal(source_path)
    destination_path = _resolve_book_destination(reviewed)

    if reviewed.action == "flag-for-judgment":
        raise RuntimeError(
            "Cannot promote a proposal marked flag-for-judgment. Review and edit it first."
        )

    if reviewed.action == "new-entry" and destination_path.exists():
        raise FileExistsError(f"Book file already exists: {destination_path}")

    if not assume_yes:
        action = _describe_promotion_action(reviewed.action, copy_file)
        confirmed = _confirm_promotion(source_path, destination_path, action)
        if not confirmed:
            raise RuntimeError("Promotion cancelled.")

    if reviewed.action == "append-to":
        _append_reviewed_body(destination_path, reviewed.body)
        if not copy_file:
            source_path.unlink()
    else:
        if copy_file:
            shutil.copy2(source_path, destination_path)
        else:
            shutil.move(str(source_path), str(destination_path))

    print(destination_path)
    return destination_path


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and dispatch commands."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "ingest":
        output_path = run_ingest(
            path=args.path,
            message=args.message,
            model=args.model,
        )
        print(output_path)
        return 0
    if args.command == "review":
        run_review(latest=args.latest, open_files=args.open)
        return 0
    if args.command == "promote":
        run_promote(
            path=args.path,
            latest=args.latest,
            copy_file=args.copy,
            assume_yes=args.yes,
        )
        return 0
    if args.command == "sync-book":
        run_sync_book(assume_yes=args.yes)
        return 0
    if args.command == "ui":
        run_ui(host=args.host, port=args.port)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def _read_entry_title(path: Path) -> str:
    """Read a book entry title from frontmatter when present, else filename stem."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.stem

    if not lines or lines[0].strip() != "---":
        return path.stem

    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.lower().startswith("title:"):
            value = stripped.split(":", 1)[1].strip()
            if value:
                return value.strip("'\"")

    return path.stem


def list_inbox_markdown_files(inbox_dir: Path | None = None) -> list[Path]:
    """Return inbox markdown files newest first, excluding scaffold files."""
    active_inbox_dir = inbox_dir or INBOX_DIR
    files = [
        path
        for path in active_inbox_dir.glob("*.md")
        if path.name not in INBOX_SCAFFOLD_FILES
    ]
    return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)


def _resolve_latest_inbox_file(inbox_dir: Path | None = None) -> Path:
    """Resolve the newest inbox markdown file."""
    files = list_inbox_markdown_files(inbox_dir)
    if not files:
        raise FileNotFoundError("No inbox markdown files are available for review.")
    return files[0]


def _resolve_inbox_markdown_path(path: str | None) -> Path:
    """Resolve an inbox markdown path from an explicit CLI argument."""
    if not path:
        raise ValueError("An inbox file path is required unless --latest is used.")

    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        if candidate.parts and candidate.parts[0] == INBOX_DIR.name:
            candidate = REPO_ROOT / candidate
        else:
            candidate = INBOX_DIR / candidate

    resolved = candidate.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Inbox file does not exist: {resolved}")
    if resolved.suffix.lower() != ".md":
        raise ValueError(f"Inbox file must be markdown: {resolved}")
    if resolved.parent != INBOX_DIR:
        raise ValueError(f"Inbox file must live in {INBOX_DIR}: {resolved}")
    if resolved.name in INBOX_SCAFFOLD_FILES:
        raise ValueError(f"Inbox scaffold files cannot be promoted: {resolved.name}")
    return resolved


def _confirm_promotion(source_path: Path, destination_path: Path, action: str) -> bool:
    """Prompt for explicit human confirmation before admission into the book."""
    response = input(
        f"{action.capitalize()} reviewed proposal into book?\n"
        f"From: {source_path}\n"
        f"To:   {destination_path}\n"
        "[y/N]: "
    )
    return response.strip().lower() in {"y", "yes"}


def _open_path(path: Path) -> None:
    """Open a file in the system default app."""
    subprocess.run(["open", str(path)], check=True)


def _read_reviewed_proposal(path: Path) -> ReviewedProposal:
    """Parse the minimal action metadata and markdown body from a reviewed inbox file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Reviewed inbox file is missing front-matter: {path}")

    closing_marker = text.find("\n---\n", 4)
    if closing_marker == -1:
        raise ValueError(f"Reviewed inbox file has malformed front-matter: {path}")

    front_matter = text[4:closing_marker]
    body = text[closing_marker + len("\n---\n") :].lstrip("\n").rstrip()

    action = _extract_frontmatter_value(front_matter, "action")
    if not action:
        raise ValueError(f"Reviewed inbox file is missing proposal.action: {path}")

    target_entry = _extract_frontmatter_value(front_matter, "target_entry")
    return ReviewedProposal(
        source_path=path,
        action=action,
        target_entry=target_entry,
        body=body,
    )


def _extract_frontmatter_value(front_matter: str, key: str) -> str | None:
    """Extract a simple scalar value from YAML-like front-matter."""
    needle = f"{key}:"
    for line in front_matter.splitlines():
        stripped = line.strip()
        if stripped.startswith(needle):
            value = stripped.split(":", 1)[1].strip()
            return value.strip("'\"") if value else None
    return None


def _resolve_book_destination(reviewed: ReviewedProposal) -> Path:
    """Resolve the destination book file for a reviewed proposal."""
    if reviewed.action == "append-to":
        if not reviewed.target_entry:
            raise ValueError("append-to proposals must include target_entry.")

        for path in sorted(BOOK_DIR.glob("*.md")):
            if path.name in BOOK_SCAFFOLD_FILES:
                continue
            if _read_entry_title(path) == reviewed.target_entry or path.stem == reviewed.target_entry:
                return path

        raise FileNotFoundError(
            f"Could not find target book entry for append-to proposal: {reviewed.target_entry}"
        )

    return BOOK_DIR / reviewed.source_path.name


def _append_reviewed_body(destination_path: Path, body: str) -> None:
    """Append reviewed proposal body content into an existing book entry."""
    existing_text = destination_path.read_text(encoding="utf-8").rstrip()
    appended_text = f"{existing_text}\n\n---\n\n{body.rstrip()}\n"
    destination_path.write_text(appended_text, encoding="utf-8")


def _describe_promotion_action(action: str, copy_file: bool) -> str:
    """Describe the human-controlled admission action for confirmation text."""
    if action == "append-to":
        return "append and keep source in inbox" if copy_file else "append and remove source from inbox"
    return "copy" if copy_file else "move"


def run_sync_book(book_dir: Path | None = None, assume_yes: bool = False) -> tuple[Path, Path]:
    """Rebuild _index.md and _topics.md from canonical book entry metadata."""
    active_book_dir = book_dir or BOOK_DIR
    entries = load_book_entries(active_book_dir)
    index_path = active_book_dir / "_index.md"
    topics_path = active_book_dir / "_topics.md"
    index_text = render_book_index(entries)
    topics_text = render_book_topics(entries)

    if not assume_yes:
        confirmed = input(
            f"Rebuild book index files?\n"
            f"Index:  {index_path}\n"
            f"Topics: {topics_path}\n"
            "[y/N]: "
        )
        if confirmed.strip().lower() not in {"y", "yes"}:
            raise RuntimeError("Book sync cancelled.")

    index_path.write_text(index_text, encoding="utf-8")
    topics_path.write_text(topics_text, encoding="utf-8")
    print(index_path)
    print(topics_path)
    return index_path, topics_path


def load_book_entries(book_dir: Path | None = None) -> list[BookEntryMetadata]:
    """Load canonical book entry metadata from front-matter."""
    active_book_dir = book_dir or BOOK_DIR
    entries: list[BookEntryMetadata] = []
    for path in sorted(active_book_dir.glob("*.md")):
        if path.name in BOOK_SCAFFOLD_FILES:
            continue
        entries.append(_parse_book_entry_metadata(path))
    return entries


def render_book_index(entries: list[BookEntryMetadata]) -> str:
    """Render book/_index.md from canonical entry metadata."""
    section_map = [
        ("thinker", "Thinkers I'm studying"),
        ("project-study", "Projects I've built"),
        ("field-study", "Fields I'm tracking"),
        ("idea-study", "Ideas I've pressure-tested"),
    ]

    lines = [
        "# Commonplace — Index",
        "",
        "A library of entries worth keeping. Annotated, grouped loosely by kind.",
        "For querying by theme rather than by entry, see `_topics.md`.",
        "",
    ]

    for kind, heading in section_map:
        lines.append(f"## {heading}")
        lines.append("")
        matching_entries = [entry for entry in entries if entry.kind == kind]
        if not matching_entries:
            lines.append("*None yet.*")
            lines.append("")
            continue

        for entry in matching_entries:
            lines.append(f"- **{entry.title}**")
            lines.extend(_wrap_bullet_continuation(entry.why_kept))
            lines.append("")

    lines.append("## Attic")
    lines.append("")
    lines.append("Entries I've outgrown. None yet.")
    lines.append("")
    return "\n".join(lines)


def render_book_topics(entries: list[BookEntryMetadata]) -> str:
    """Render book/_topics.md from canonical entry metadata."""
    topic_map: dict[str, list[BookEntryMetadata]] = {}
    for entry in entries:
        for topic in entry.topics:
            topic_map.setdefault(topic, []).append(entry)

    lines = [
        "# Topics",
        "",
        "A controlled vocabulary of themes that recur across entries. Use this",
        "when querying by theme rather than browsing by entry. Slugs in",
        "`kebab-case` are what entries reference in their `topics:` front-matter.",
        "",
        "A topic earns a place here only when at least two entries carry it.",
        "",
        "---",
        "",
    ]

    rendered_any = False
    for topic in sorted(topic for topic, topic_entries in topic_map.items() if len(topic_entries) >= 2):
        rendered_any = True
        lines.append(f"## {topic}")
        lines.append("")
        for entry in topic_map[topic]:
            lines.append(f"- {entry.title}")
        lines.append("")

    if not rendered_any:
        lines.append("*No recurring topics yet.*")
        lines.append("")

    return "\n".join(lines)


def _parse_book_entry_metadata(path: Path) -> BookEntryMetadata:
    """Parse the required metadata fields from a canonical book entry."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Book entry is missing front-matter: {path}")

    closing_marker = text.find("\n---\n", 4)
    if closing_marker == -1:
        raise ValueError(f"Book entry has malformed front-matter: {path}")

    front_matter = text[4:closing_marker]
    metadata = _parse_simple_frontmatter(front_matter)
    title = metadata.get("title")
    kind = metadata.get("kind")
    why_kept = metadata.get("why-kept")
    topics = _parse_topics_value(metadata.get("topics"))

    if not title or not kind or not why_kept:
        raise ValueError(f"Book entry is missing required metadata: {path}")

    return BookEntryMetadata(
        path=path,
        title=title,
        kind=kind,
        why_kept=why_kept,
        topics=topics,
    )


def _parse_simple_frontmatter(front_matter: str) -> dict[str, str]:
    """Parse simple front-matter scalars and folded continuations."""
    data: dict[str, str] = {}
    current_key: str | None = None

    for raw_line in front_matter.splitlines():
        if raw_line.startswith((" ", "\t")) and current_key:
            continuation = raw_line.strip()
            if continuation:
                data[current_key] = f"{data[current_key]} {continuation}".strip()
            continue

        if ":" not in raw_line:
            current_key = None
            continue

        key, value = raw_line.split(":", 1)
        current_key = key.strip()
        data[current_key] = value.strip()

    return data


def _parse_topics_value(value: str | None) -> list[str]:
    """Parse the compact topics front-matter list."""
    if not value:
        return []
    stripped = value.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        inner = stripped[1:-1].strip()
        if not inner:
            return []
        return [item.strip() for item in inner.split(",") if item.strip()]
    return [stripped]


def _wrap_bullet_continuation(text: str, width: int = 72) -> list[str]:
    """Wrap descriptive bullet continuation lines in the book index."""
    return [f"  {line}" for line in textwrap.wrap(text, width=width)]


def run_ui(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Launch the local-only Commonplace web UI."""
    if host != "127.0.0.1":
        raise ValueError("Commonplace UI must bind to 127.0.0.1 only.")

    from uvicorn import run as uvicorn_run

    from .ui.app import create_app

    url = f"http://{host}:{port}"
    webbrowser.open(url)
    uvicorn_run(create_app(), host=host, port=port)


if __name__ == "__main__":
    raise SystemExit(main())

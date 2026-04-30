"""Command-line interface for the Commonplace ingestion workflow."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

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
        default=DEFAULT_PROPOSAL_MODEL,
        help="OpenAI model to use for proposal generation.",
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
        display_path=str(extracted.path),
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


if __name__ == "__main__":
    raise SystemExit(main())

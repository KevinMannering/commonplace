"""CLI entrypoint for Commonplace."""

import argparse
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

from .extractor import DEFAULT_MODEL, ExtractionError, extract_session
from .ingest import InputError, load_input
from .markdown import render_markdown


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WIKI_DIR = PROJECT_ROOT / "wiki"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    lowered = normalized.lower()
    compact = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return compact or "untitled-session"


def build_output_path(wiki_dir: Path, title: str) -> Path:
    datestamp = datetime.now().strftime("%Y-%m-%d")
    return wiki_dir / f"{datestamp}-{slugify(title)}.md"


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="commonplace", description="Extract transcripts into wiki pages.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract", help="Extract a transcript into a structured wiki page.")
    extract_parser.add_argument("--type", choices=["strategy", "research"], required=True, dest="session_type")
    extract_parser.add_argument(
        "--input",
        default="-",
        help="Transcript source: file path, shared ChatGPT/Claude URL, or '-' / omitted for stdin.",
    )
    extract_parser.add_argument("--title", default="", help="Optional title hint for the generated wiki page.")
    extract_parser.add_argument("--wiki-dir", default=str(DEFAULT_WIKI_DIR), help="Directory where markdown pages are written.")
    return parser


def main(argv=None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        loaded = load_input(args.input)
    except InputError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not loaded.transcript:
        parser.error("Transcript input is empty.")

    wiki_dir = Path(args.wiki_dir)
    wiki_dir.mkdir(parents=True, exist_ok=True)

    try:
        extracted = extract_session(
            transcript=loaded.transcript,
            session_type=args.session_type,
            title_hint=args.title or loaded.title_hint,
        )
    except ExtractionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output_path = build_output_path(wiki_dir, extracted["title"])
    markdown = render_markdown(
        data=extracted,
        session_type=args.session_type,
        transcript_path=loaded.source_label,
        model=extracted.get("_model", DEFAULT_MODEL),
    )
    output_path.write_text(markdown, encoding="utf-8")

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

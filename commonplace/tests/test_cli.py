"""Tests for the Commonplace CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from commonplace import cli


def test_parser_accepts_ingest_with_message() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(["ingest", "source.md", "-m", "why this matters"])

    assert args.command == "ingest"
    assert args.path == "source.md"
    assert args.message == "why this matters"


def test_main_writes_inbox_file_with_monkeypatched_flow(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    book_dir = tmp_path / "book"
    inbox_dir = tmp_path / "inbox"
    book_dir.mkdir()
    book_dir.joinpath("_index.md").write_text("Index text", encoding="utf-8")
    book_dir.joinpath("_topics.md").write_text("Topics text", encoding="utf-8")
    book_dir.joinpath("Existing Entry.md").write_text(
        "---\ntitle: Existing Entry\n---\n",
        encoding="utf-8",
    )
    source_path = tmp_path / "source.md"
    source_path.write_text("Source body", encoding="utf-8")

    monkeypatch.setattr(cli, "BOOK_DIR", book_dir)
    monkeypatch.setattr(cli, "INBOX_DIR", inbox_dir)

    @dataclass(frozen=True)
    class FakeExtractedSource:
        path: Path
        filename: str
        content_text: str

    @dataclass(frozen=True)
    class FakeProposal:
        action: str
        target_entry: str | None
        draft_title: str | None
        draft_content: str
        reasoning: str
        confidence: str

    def fake_extract_text(path: Path) -> FakeExtractedSource:
        assert path == source_path.resolve()
        return FakeExtractedSource(
            path=path,
            filename=path.name,
            content_text="Extracted body",
        )

    def fake_propose_entry(source_text: str, book_context, message: str | None, model: str):
        assert source_text == "Extracted body"
        assert book_context.index_text == "Index text"
        assert book_context.topics_text == "Topics text"
        assert book_context.entry_titles == ["Existing Entry"]
        assert message == "why this matters"
        assert model == "test-model"
        return FakeProposal(
            action="new-entry",
            target_entry=None,
            draft_title="Test Entry",
            draft_content="# Test Entry\n",
            reasoning="Reasoning",
            confidence="high",
        )

    def fake_render_inbox_markdown(proposal, source) -> str:
        assert proposal.draft_title == "Test Entry"
        assert source.filename == "source.md"
        assert source.message == "why this matters"
        return "---\nsource:\n  file: source.md\n---\n\n# Test Entry\n"

    def fake_suggest_inbox_filename(proposal, for_date, fallback_stem: str) -> str:
        assert proposal.draft_title == "Test Entry"
        assert fallback_stem == "source"
        return "2026-04-29-test-entry.md"

    monkeypatch.setattr(cli, "extract_text", fake_extract_text)
    monkeypatch.setattr(cli, "propose_entry", fake_propose_entry)
    monkeypatch.setattr(cli, "render_inbox_markdown", fake_render_inbox_markdown)
    monkeypatch.setattr(cli, "suggest_inbox_filename", fake_suggest_inbox_filename)

    exit_code = cli.main(
        ["ingest", str(source_path), "-m", "why this matters", "--model", "test-model"]
    )

    created_path = inbox_dir / "2026-04-29-test-entry.md"
    assert exit_code == 0
    assert created_path.exists()
    assert created_path.read_text(encoding="utf-8").endswith("# Test Entry\n")
    assert str(created_path) in capsys.readouterr().out


def test_discover_entry_titles_excludes_scaffold_files(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    book_dir.joinpath("README.md").write_text("# Book\n", encoding="utf-8")
    book_dir.joinpath("CONVENTIONS.md").write_text("# Rules\n", encoding="utf-8")
    book_dir.joinpath("_index.md").write_text("index", encoding="utf-8")
    book_dir.joinpath("_topics.md").write_text("topics", encoding="utf-8")
    book_dir.joinpath(".gitkeep").write_text("", encoding="utf-8")
    book_dir.joinpath("Entry One.md").write_text(
        "---\ntitle: Entry One Title\n---\n",
        encoding="utf-8",
    )
    book_dir.joinpath("Entry Two.md").write_text("# Entry Two\n", encoding="utf-8")

    titles = cli.discover_entry_titles(book_dir)

    assert titles == ["Entry One Title", "Entry Two"]

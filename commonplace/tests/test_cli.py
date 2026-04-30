"""Tests for the Commonplace CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

import pytest

from commonplace import cli


def test_parser_accepts_ingest_with_message() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(["ingest", "source.md", "-m", "why this matters"])

    assert args.command == "ingest"
    assert args.path == "source.md"
    assert args.message == "why this matters"


def test_parser_accepts_review_and_promote_options() -> None:
    parser = cli.build_parser()

    review_args = parser.parse_args(["review", "--latest", "--open"])
    promote_args = parser.parse_args(["promote", "--latest", "--copy", "--yes"])

    assert review_args.command == "review"
    assert review_args.latest is True
    assert review_args.open is True
    assert promote_args.command == "promote"
    assert promote_args.latest is True
    assert promote_args.copy is True
    assert promote_args.yes is True


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


def test_review_lists_inbox_files_newest_first_and_can_open(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    inbox_dir = tmp_path / "inbox"
    inbox_dir.mkdir()
    older = inbox_dir / "2026-04-29-older.md"
    newer = inbox_dir / "2026-04-30-newer.md"
    readme = inbox_dir / "README.md"
    older.write_text("older", encoding="utf-8")
    newer.write_text("newer", encoding="utf-8")
    readme.write_text("scaffold", encoding="utf-8")
    os.utime(older, (100, 100))
    os.utime(newer, (200, 200))

    opened: list[Path] = []

    monkeypatch.setattr(cli, "INBOX_DIR", inbox_dir)
    monkeypatch.setattr(cli, "_open_path", lambda path: opened.append(path))

    selected = cli.run_review(latest=False, open_files=True)

    assert selected == [newer, older]
    assert opened == [newer, older]
    assert capsys.readouterr().out.splitlines() == [str(newer), str(older)]


def test_review_latest_only_returns_newest_file(tmp_path: Path, monkeypatch, capsys) -> None:
    inbox_dir = tmp_path / "inbox"
    inbox_dir.mkdir()
    older = inbox_dir / "older.md"
    newer = inbox_dir / "newer.md"
    older.write_text("older", encoding="utf-8")
    newer.write_text("newer", encoding="utf-8")
    os.utime(older, (100, 100))
    os.utime(newer, (200, 200))

    monkeypatch.setattr(cli, "INBOX_DIR", inbox_dir)

    selected = cli.run_review(latest=True, open_files=False)

    assert selected == [newer]
    assert capsys.readouterr().out.strip() == str(newer)


def test_promote_latest_moves_file_when_confirmed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    inbox_dir = tmp_path / "inbox"
    book_dir = tmp_path / "book"
    inbox_dir.mkdir()
    book_dir.mkdir()
    proposal = inbox_dir / "2026-04-30-proposal.md"
    proposal.write_text(
        "---\n"
        "proposal:\n"
        "  action: new-entry\n"
        "source:\n"
        '  file: "source.pdf"\n'
        "---\n\n"
        "proposal\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cli, "INBOX_DIR", inbox_dir)
    monkeypatch.setattr(cli, "BOOK_DIR", book_dir)
    monkeypatch.setattr("builtins.input", lambda _: "y")

    promoted = cli.run_promote(latest=True, copy_file=False, assume_yes=False)

    destination = book_dir / proposal.name
    assert promoted == destination
    assert destination.exists()
    assert not proposal.exists()
    assert capsys.readouterr().out.strip() == str(destination)


def test_promote_copy_preserves_inbox_file_when_yes_is_passed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    inbox_dir = tmp_path / "inbox"
    book_dir = tmp_path / "book"
    inbox_dir.mkdir()
    book_dir.mkdir()
    proposal = inbox_dir / "2026-04-30-proposal.md"
    proposal.write_text(
        "---\n"
        "proposal:\n"
        "  action: new-entry\n"
        "source:\n"
        '  file: "source.pdf"\n'
        "---\n\n"
        "proposal\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cli, "INBOX_DIR", inbox_dir)
    monkeypatch.setattr(cli, "BOOK_DIR", book_dir)

    promoted = cli.run_promote(
        path=str(proposal),
        latest=False,
        copy_file=True,
        assume_yes=True,
    )

    destination = book_dir / proposal.name
    assert promoted == destination
    assert destination.exists()
    assert proposal.exists()
    assert destination.read_text(encoding="utf-8").endswith("proposal\n")
    assert capsys.readouterr().out.strip() == str(destination)


def test_promote_append_to_appends_body_into_target_entry(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    inbox_dir = tmp_path / "inbox"
    book_dir = tmp_path / "book"
    inbox_dir.mkdir()
    book_dir.mkdir()
    proposal = inbox_dir / "2026-04-30-proposal.md"
    proposal.write_text(
        "---\n"
        "proposal:\n"
        '  action: append-to\n'
        '  target_entry: "Existing Entry"\n'
        "source:\n"
        '  file: "source.pdf"\n'
        "---\n\n"
        "## Appended Material\n\nUseful addition.\n",
        encoding="utf-8",
    )
    target = book_dir / "Existing Entry.md"
    target.write_text(
        "---\ntitle: Existing Entry\n---\n\n# Existing Entry\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cli, "INBOX_DIR", inbox_dir)
    monkeypatch.setattr(cli, "BOOK_DIR", book_dir)

    promoted = cli.run_promote(
        path=str(proposal),
        latest=False,
        copy_file=False,
        assume_yes=True,
    )

    updated_text = target.read_text(encoding="utf-8")
    assert promoted == target
    assert "## Appended Material" in updated_text
    assert "Useful addition." in updated_text
    assert "---\n\n## Appended Material" in updated_text
    assert not proposal.exists()
    assert capsys.readouterr().out.strip() == str(target)


def test_promote_flag_for_judgment_refuses_automatic_admission(
    tmp_path: Path, monkeypatch
) -> None:
    inbox_dir = tmp_path / "inbox"
    book_dir = tmp_path / "book"
    inbox_dir.mkdir()
    book_dir.mkdir()
    proposal = inbox_dir / "2026-04-30-proposal.md"
    proposal.write_text(
        "---\n"
        "proposal:\n"
        "  action: flag-for-judgment\n"
        "source:\n"
        '  file: "source.pdf"\n'
        "---\n\n"
        "Needs review.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cli, "INBOX_DIR", inbox_dir)
    monkeypatch.setattr(cli, "BOOK_DIR", book_dir)

    with pytest.raises(RuntimeError, match="flag-for-judgment"):
        cli.run_promote(
            path=str(proposal),
            latest=False,
            copy_file=False,
            assume_yes=True,
        )


def test_sync_book_rebuilds_index_and_topics_from_entry_metadata(
    tmp_path: Path, capsys
) -> None:
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    (book_dir / "README.md").write_text("book readme", encoding="utf-8")
    (book_dir / "CONVENTIONS.md").write_text("rules", encoding="utf-8")
    (book_dir / ".gitkeep").write_text("", encoding="utf-8")
    (book_dir / "_index.md").write_text("stale index", encoding="utf-8")
    (book_dir / "_topics.md").write_text("stale topics", encoding="utf-8")

    (book_dir / "Thinker Entry.md").write_text(
        "---\n"
        "title: Thinker Entry\n"
        "kind: thinker\n"
        "why-kept: Tracks a thinker's reusable moves.\n"
        "topics: [shared-topic, thinker-studies]\n"
        "---\n\n"
        "# Thinker Entry\n",
        encoding="utf-8",
    )
    (book_dir / "Field Entry.md").write_text(
        "---\n"
        "title: Field Entry\n"
        "kind: field-study\n"
        "why-kept: Living field record with appended updates.\n"
        "topics: [shared-topic, field-work]\n"
        "---\n\n"
        "# Field Entry\n\n"
        "---\n\n"
        "## Additions\n\n"
        "Appended material.\n",
        encoding="utf-8",
    )

    index_path, topics_path = cli.run_sync_book(book_dir=book_dir, assume_yes=True)

    index_text = index_path.read_text(encoding="utf-8")
    topics_text = topics_path.read_text(encoding="utf-8")

    assert "## Thinkers I'm studying" in index_text
    assert "**Thinker Entry**" in index_text
    assert "Tracks a thinker's reusable moves." in index_text
    assert "## Fields I'm tracking" in index_text
    assert "**Field Entry**" in index_text
    assert "Living field record with appended updates." in index_text
    assert "stale index" not in index_text

    assert "## shared-topic" in topics_text
    assert "- Thinker Entry" in topics_text
    assert "- Field Entry" in topics_text
    assert "## thinker-studies" not in topics_text
    assert "stale topics" not in topics_text
    assert capsys.readouterr().out.splitlines() == [str(index_path), str(topics_path)]


def test_parser_accepts_sync_book_yes_flag() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(["sync-book", "--yes"])

    assert args.command == "sync-book"
    assert args.yes is True

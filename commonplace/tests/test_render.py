"""Tests for inbox markdown rendering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from commonplace.render import (
    SourceMetadata,
    render_inbox_markdown,
    suggest_inbox_filename,
)


@dataclass(frozen=True)
class FakeProposal:
    action: str
    target_entry: str | None
    draft_title: str | None
    draft_content: str
    reasoning: str
    confidence: str


def test_append_to_render_includes_target_entry_and_front_matter() -> None:
    proposal = FakeProposal(
        action="append-to",
        target_entry="Existing Entry",
        draft_title="Ignored Here",
        draft_content="## Addition\n\nUseful material.",
        reasoning="This clearly extends an existing entry.",
        confidence="high",
    )
    source = SourceMetadata(
        filename="source-file.pdf",
        ingested_at=datetime(2026, 4, 29, 22, 0, tzinfo=timezone.utc),
        message="why this matters",
    )

    rendered = render_inbox_markdown(proposal, source)

    assert rendered.startswith("---\n")
    assert "\n---\n\n" in rendered
    assert '  target_entry: "Existing Entry"' in rendered
    assert "  action: append-to" in rendered
    assert "  confidence: high" in rendered


def test_render_omits_optional_message_when_not_provided() -> None:
    proposal = FakeProposal(
        action="new-entry",
        target_entry=None,
        draft_title="Durable Idea",
        draft_content="# Durable Idea\n",
        reasoning="It stands on its own.",
        confidence="medium",
    )
    source = SourceMetadata(
        filename="notes.md",
        ingested_at=datetime(2026, 4, 29, 22, 0, tzinfo=timezone.utc),
        message=None,
    )

    rendered = render_inbox_markdown(proposal, source)

    assert "  message:" not in rendered
    assert "# Durable Idea\n" in rendered
    assert rendered.endswith("\n")


def test_rendered_body_contains_draft_content() -> None:
    proposal = FakeProposal(
        action="flag-for-judgment",
        target_entry=None,
        draft_title=None,
        draft_content="Body stays exactly here.\n\nSecond paragraph.",
        reasoning="The case is ambiguous.",
        confidence="low",
    )
    source = SourceMetadata(
        filename="ambiguous.txt",
        ingested_at=datetime(2026, 4, 29, 22, 0, tzinfo=timezone.utc),
    )

    rendered = render_inbox_markdown(proposal, source)

    assert "Body stays exactly here.\n\nSecond paragraph." in rendered


def test_suggested_filename_uses_date_and_slug() -> None:
    proposal = FakeProposal(
        action="new-entry",
        target_entry=None,
        draft_title="Some Draft Title!",
        draft_content="content",
        reasoning="reasoning",
        confidence="high",
    )

    filename = suggest_inbox_filename(proposal, date(2026, 4, 29))

    assert filename == "2026-04-29-some-draft-title.md"

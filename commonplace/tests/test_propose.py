"""Tests for proposal generation."""

from __future__ import annotations

from dataclasses import dataclass

from commonplace.propose import BookContext, build_user_prompt, propose_entry


def test_build_user_prompt_includes_all_major_sections() -> None:
    book_context = BookContext(
        index_text="Index summary",
        topics_text="topic-a\ntopic-b",
        entry_titles=["Entry One", "Entry Two"],
    )

    prompt = build_user_prompt(
        source_text="Source body",
        message="Why this matters",
        book_context=book_context,
    )

    assert "Human message" in prompt
    assert "Why this matters" in prompt
    assert "Book index" in prompt
    assert "Index summary" in prompt
    assert "Book topics" in prompt
    assert "topic-a" in prompt
    assert "Existing entry titles" in prompt
    assert "- Entry One" in prompt
    assert "Source text" in prompt
    assert "Source body" in prompt


def test_build_user_prompt_handles_missing_human_message() -> None:
    book_context = BookContext(
        index_text="Index summary",
        topics_text="topic-a",
        entry_titles=[],
    )

    prompt = build_user_prompt(
        source_text="Source body",
        message=None,
        book_context=book_context,
    )

    assert "Human message" in prompt
    assert "(none provided)" in prompt
    assert "Existing entry titles" in prompt
    assert "(none)" in prompt


def test_propose_entry_returns_structured_proposal_with_mocked_client(monkeypatch) -> None:
    book_context = BookContext(
        index_text="Index summary",
        topics_text="topic-a",
        entry_titles=["Entry One"],
    )

    @dataclass(frozen=True)
    class FakeProposal:
        action: str
        target_entry: str | None
        draft_title: str | None
        draft_kind: str
        draft_topics: list[str]
        draft_why_kept: str
        draft_content: str
        reasoning: str
        confidence: str

        @classmethod
        def model_validate(cls, value: object) -> FakeProposal:
            if isinstance(value, cls):
                return value
            if isinstance(value, dict):
                return cls(**value)
            raise TypeError("Unsupported proposal payload.")

    def fake_get_prompt_contract() -> tuple[type[FakeProposal], str]:
        return FakeProposal, "system prompt"

    class FakeParsedItem:
        type = "output_text"

        def __init__(self, parsed: FakeProposal) -> None:
            self.parsed = parsed

    class FakeMessage:
        type = "message"

        def __init__(self, parsed: FakeProposal) -> None:
            self.content = [FakeParsedItem(parsed)]

    class FakeResponse:
        def __init__(self, parsed: FakeProposal) -> None:
            self.output = [FakeMessage(parsed)]

    class FakeResponsesAPI:
        def parse(self, **kwargs):
            assert kwargs["model"] == "test-model"
            assert kwargs["input"][0]["role"] == "system"
            assert kwargs["input"][1]["role"] == "user"
            assert "Book index" in kwargs["input"][1]["content"]
            assert kwargs["text_format"] is FakeProposal
            return FakeResponse(
                FakeProposal(
                    action="new-entry",
                    target_entry=None,
                    draft_title="Test Entry",
                    draft_kind="idea-study",
                    draft_topics=["topic-a"],
                    draft_why_kept="It is worth keeping.",
                    draft_content="# Test Entry\n",
                    reasoning="It stands on its own.",
                    confidence="high",
                )
            )

    class FakeClient:
        def __init__(self) -> None:
            self.responses = FakeResponsesAPI()

    monkeypatch.setattr("commonplace.propose._get_prompt_contract", fake_get_prompt_contract)

    proposal = propose_entry(
        source_text="Source body",
        book_context=book_context,
        message="Why this matters",
        model="test-model",
        client=FakeClient(),
    )

    assert isinstance(proposal, FakeProposal)
    assert proposal.action == "new-entry"
    assert proposal.draft_title == "Test Entry"

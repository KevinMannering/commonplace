"""Tests for proposal generation."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from commonplace.config import COMMONPLACE_CONFIG
from commonplace.propose import (
    BookContext,
    _build_client,
    _collect_escalation_triggers,
    _should_escalate,
    build_user_prompt,
    propose_entry,
)


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
        needs_escalation: bool

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
                    needs_escalation=False,
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


def test_propose_entry_escalates_from_fast_to_smart_model(monkeypatch) -> None:
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
        needs_escalation: bool

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
        def __init__(self) -> None:
            self.calls: list[str] = []

        def parse(self, **kwargs):
            self.calls.append(kwargs["model"])
            if kwargs["model"] == COMMONPLACE_CONFIG.fast_model:
                return FakeResponse(
                    FakeProposal(
                        action="flag-for-judgment",
                        target_entry=None,
                        draft_title=None,
                        draft_kind="idea-study",
                        draft_topics=["topic-a"],
                        draft_why_kept="The case needs a second look.",
                        draft_content="Draft one",
                        reasoning="Ambiguous first pass.",
                        confidence="low",
                        needs_escalation=True,
                    )
                )

            return FakeResponse(
                FakeProposal(
                    action="new-entry",
                    target_entry=None,
                    draft_title="Escalated Entry",
                    draft_kind="idea-study",
                    draft_topics=["topic-a"],
                    draft_why_kept="The larger model resolved the ambiguity.",
                    draft_content="Draft two",
                    reasoning="Second pass resolved the case.",
                    confidence="high",
                    needs_escalation=False,
                )
            )

    class FakeClient:
        def __init__(self) -> None:
            self.responses = FakeResponsesAPI()

    monkeypatch.setattr("commonplace.propose._get_prompt_contract", fake_get_prompt_contract)

    client = FakeClient()
    proposal = propose_entry(
        source_text="Source body",
        book_context=book_context,
        message=None,
        client=client,
    )

    assert proposal.draft_title == "Escalated Entry"
    assert client.responses.calls == [
        COMMONPLACE_CONFIG.fast_model,
        COMMONPLACE_CONFIG.smart_model,
    ]


def test_build_client_raises_clear_error_when_api_key_is_missing(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("commonplace.propose.load_dotenv", lambda dotenv_path=None: None)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is missing"):
        _build_client()


def test_build_client_reads_api_key_from_environment(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class FakeOpenAI:
        def __init__(self, api_key: str) -> None:
            captured["api_key"] = api_key

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("commonplace.propose.load_dotenv", lambda dotenv_path=None: None)
    monkeypatch.setattr("commonplace.propose.OpenAI", FakeOpenAI)

    client = _build_client()

    assert isinstance(client, FakeOpenAI)
    assert captured["api_key"] == "test-key"


def test_default_proposal_model_comes_from_shared_config() -> None:
    from commonplace.propose import DEFAULT_PROPOSAL_MODEL

    assert DEFAULT_PROPOSAL_MODEL == COMMONPLACE_CONFIG.fast_model


def test_should_escalate_uses_centralized_rules() -> None:
    @dataclass(frozen=True)
    class FakeProposal:
        action: str
        target_entry: str | None
        draft_topics: list[str]
        confidence: str
        needs_escalation: bool

    proposal = FakeProposal(
        action="flag-for-judgment",
        target_entry=None,
        draft_topics=["a", "b", "c"],
        confidence="low",
        needs_escalation=True,
    )

    triggers = _collect_escalation_triggers(proposal)

    assert "model-requested-escalation" in triggers
    assert "low-confidence" in triggers
    assert "flag-for-judgment" in triggers
    assert "broad-topic-spread" in triggers
    assert _should_escalate(proposal) is True

"""Schema and prompt contract for Commonplace proposal generation.

This module defines the system prompt used to draft inbox proposals, the
structured proposal schema returned by the model, and the small enums and
constants that support that contract.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProposalAction(str, Enum):
    """The editorial action the model may recommend."""

    NEW_ENTRY = "new-entry"
    APPEND_TO = "append-to"
    FLAG_FOR_JUDGMENT = "flag-for-judgment"


class DraftKind(str, Enum):
    """The kinds of durable entries Commonplace accepts."""

    THINKER = "thinker"
    PROJECT_STUDY = "project-study"
    FIELD_STUDY = "field-study"
    IDEA_STUDY = "idea-study"


class ConfidenceLevel(str, Enum):
    """The model's confidence in its recommendation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


DRAFT_KIND_DESCRIPTIONS: dict[DraftKind, str] = {
    DraftKind.THINKER: "An entry centered on a person and the ideas worth keeping from them.",
    DraftKind.PROJECT_STUDY: "An entry about a project, build, or concrete line of work.",
    DraftKind.FIELD_STUDY: "An entry that captures a domain, discipline, or body of practice.",
    DraftKind.IDEA_STUDY: "An entry for a concept, framework, or claim worth returning to.",
}


class Proposal(BaseModel):
    """Structured proposal for a candidate addition to Commonplace."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    action: ProposalAction = Field(
        description=(
            "Choose whether the source should become a new entry, extend an "
            "existing entry, or be flagged for human judgment."
        )
    )
    target_entry: str | None = Field(
        default=None,
        description=(
            "The title of the existing book entry to append to. Required only "
            "when action is 'append-to'."
        ),
    )
    draft_title: str | None = Field(
        default=None,
        description=(
            "The proposed entry title. Expected for new entries and optional "
            "when extending an existing one."
        ),
    )
    draft_kind: DraftKind = Field(
        description="The kind of entry the proposal belongs to."
    )
    draft_topics: list[str] = Field(
        default_factory=list,
        description="A short list of topic labels that place the proposal in the book.",
    )
    draft_why_kept: str = Field(
        min_length=1,
        description="A brief explanation of why this material belongs in the library.",
    )
    draft_content: str = Field(
        min_length=1,
        description="The proposed markdown body for the entry or addition.",
    )
    reasoning: str = Field(
        min_length=1,
        description="Why this action was chosen in light of the source and book context.",
    )
    confidence: ConfidenceLevel = Field(
        description="The model's confidence in the proposal."
    )

    @model_validator(mode="after")
    def validate_action_requirements(self) -> Proposal:
        """Enforce action-dependent fields."""
        if self.action == ProposalAction.APPEND_TO and not self.target_entry:
            raise ValueError("target_entry is required when action is 'append-to'.")

        if self.action != ProposalAction.APPEND_TO and self.target_entry:
            raise ValueError(
                "target_entry may only be set when action is 'append-to'."
            )

        if self.action == ProposalAction.NEW_ENTRY and not self.draft_title:
            raise ValueError("draft_title is required when action is 'new-entry'.")

        return self


SYSTEM_PROMPT = """
You are the assistant librarian for Commonplace, a personal library of things
worth keeping.

Your task is to read a source text alongside lightweight context from the
existing book and decide what should happen next.

You must choose one of three actions:
- `new-entry` when the material deserves its own durable entry
- `append-to` when the material clearly extends an existing entry already in the book
- `flag-for-judgment` when the case is ambiguous, incomplete, or better left for direct human review

Prefer `append-to` when the incoming material substantially belongs inside an
existing entry. Avoid duplicating ideas across the library when a strong append
target already exists.

Write for a commonplace book rather than for a feed, memo, or product surface.
The result should be concise, durable, and readable as part of a personal
knowledge library. Favor clear markdown, stable language, and reasons worth
returning to later.

You will receive source text and lightweight book context. Use both. Judge the
material in relation to what the book already contains, not in isolation.

Return structured output that matches the schema exactly. Do not add extra
fields. If you choose `append-to`, include `target_entry`. If you choose
`new-entry`, include `draft_title`.
""".strip()


__all__ = [
    "ConfidenceLevel",
    "DRAFT_KIND_DESCRIPTIONS",
    "DraftKind",
    "Proposal",
    "ProposalAction",
    "SYSTEM_PROMPT",
]

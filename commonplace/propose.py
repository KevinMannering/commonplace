"""Proposal generation for turning extracted source text into Commonplace proposals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openai import OpenAI

    from .prompts import Proposal


DEFAULT_PROPOSAL_MODEL = "gpt-4o-2024-08-06"


@dataclass(frozen=True)
class BookContext:
    """Lightweight book context used to judge where new material belongs."""

    index_text: str
    topics_text: str
    entry_titles: list[str]


def build_user_prompt(
    source_text: str,
    message: str | None,
    book_context: BookContext,
) -> str:
    """Build the deterministic user payload for proposal generation."""
    entry_titles_text = "\n".join(f"- {title}" for title in book_context.entry_titles)
    if not entry_titles_text:
        entry_titles_text = "(none)"

    human_message = message.strip() if message and message.strip() else "(none provided)"

    sections = [
        "Human message",
        human_message,
        "",
        "Book index",
        book_context.index_text.strip(),
        "",
        "Book topics",
        book_context.topics_text.strip(),
        "",
        "Existing entry titles",
        entry_titles_text,
        "",
        "Source text",
        source_text.strip(),
    ]
    return "\n".join(sections).strip()


def propose_entry(
    source_text: str,
    book_context: BookContext,
    message: str | None = None,
    model: str = DEFAULT_PROPOSAL_MODEL,
    client: OpenAI | None = None,
) -> Proposal:
    """Generate a structured Commonplace proposal from source text and book context."""
    proposal_model, system_prompt = _get_prompt_contract()
    active_client = client or _build_client()
    user_prompt = build_user_prompt(
        source_text=source_text,
        message=message,
        book_context=book_context,
    )

    try:
        response = active_client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=proposal_model,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI proposal generation failed for model {model}.") from exc

    return _parse_proposal_response(response, proposal_model)


def _build_client() -> OpenAI:
    """Construct an OpenAI client on demand."""
    from openai import OpenAI

    return OpenAI()


def _get_prompt_contract() -> tuple[type[Proposal], str]:
    """Load the proposal schema and system prompt lazily."""
    from .prompts import Proposal, SYSTEM_PROMPT

    return Proposal, SYSTEM_PROMPT


def _parse_proposal_response(response: Any, proposal_model: type[Proposal]) -> Proposal:
    """Extract the parsed proposal object from a structured Responses API reply."""
    for output in response.output:
        if getattr(output, "type", None) != "message":
            continue

        for item in getattr(output, "content", []):
            item_type = getattr(item, "type", None)
            if item_type == "refusal":
                refusal_text = getattr(item, "refusal", "Model refused to answer.")
                raise RuntimeError(f"OpenAI proposal generation was refused: {refusal_text}")

            parsed = getattr(item, "parsed", None)
            if parsed is not None:
                if isinstance(parsed, proposal_model):
                    return parsed
                return proposal_model.model_validate(parsed)

    raise RuntimeError("OpenAI proposal generation returned no parsed proposal.")


__all__ = [
    "BookContext",
    "DEFAULT_PROPOSAL_MODEL",
    "build_user_prompt",
    "propose_entry",
]

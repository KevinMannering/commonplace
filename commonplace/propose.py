"""Proposal generation for turning extracted source text into Commonplace proposals."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dotenv import load_dotenv
from openai import OpenAI

from .config import COMMONPLACE_CONFIG

if TYPE_CHECKING:
    from .prompts import Proposal


DEFAULT_PROPOSAL_MODEL = COMMONPLACE_CONFIG.fast_model
REPO_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = REPO_ROOT / ".env"


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
    active_client = client or _build_client()
    user_prompt = build_user_prompt(
        source_text=source_text,
        message=message,
        book_context=book_context,
    )
    initial_model = model or COMMONPLACE_CONFIG.fast_model
    first_pass = _request_proposal(
        client=active_client,
        model=initial_model,
        user_prompt=user_prompt,
    )

    if initial_model == COMMONPLACE_CONFIG.smart_model:
        return first_pass

    if not _should_escalate(first_pass):
        return first_pass

    return _request_proposal(
        client=active_client,
        model=COMMONPLACE_CONFIG.smart_model,
        user_prompt=user_prompt,
    )


def _build_client() -> OpenAI:
    """Construct an OpenAI client on demand."""
    api_key = _load_openai_api_key()
    return OpenAI(api_key=api_key)


def _load_openai_api_key() -> str:
    """Load the OpenAI API key from the environment or repo-root .env file."""
    load_dotenv(dotenv_path=DOTENV_PATH)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    raise RuntimeError(
        "OPENAI_API_KEY is missing. Set it in the environment or add it to "
        f"{DOTENV_PATH} before running Commonplace."
    )


def _get_prompt_contract() -> tuple[type[Proposal], str]:
    """Load the proposal schema and system prompt lazily."""
    from .prompts import Proposal, SYSTEM_PROMPT

    return Proposal, SYSTEM_PROMPT


def _request_proposal(
    client: OpenAI,
    model: str,
    user_prompt: str,
) -> Proposal:
    """Request one structured proposal from a specific model."""
    proposal_model, system_prompt = _get_prompt_contract()

    try:
        response = client.responses.parse(
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


def _should_escalate(proposal: Proposal) -> bool:
    """Decide whether the fast-pass proposal should be rerun on the larger model."""
    return bool(_collect_escalation_triggers(proposal))


def _collect_escalation_triggers(proposal: Proposal) -> list[str]:
    """Collect the configured escalation triggers that apply to a proposal."""
    triggers: list[str] = []
    enabled_triggers = set(COMMONPLACE_CONFIG.escalation_triggers)

    if proposal.needs_escalation and "model-requested-escalation" in enabled_triggers:
        triggers.append("model-requested-escalation")

    if (
        str(getattr(proposal.confidence, "value", proposal.confidence))
        == COMMONPLACE_CONFIG.low_confidence_threshold
        and "low-confidence" in enabled_triggers
    ):
        triggers.append("low-confidence")

    if (
        str(getattr(proposal.action, "value", proposal.action)) == "flag-for-judgment"
        and "flag-for-judgment" in enabled_triggers
    ):
        triggers.append("flag-for-judgment")

    if (
        str(getattr(proposal.action, "value", proposal.action)) == "append-to"
        and proposal.target_entry is None
        and "ambiguous-append-target" in enabled_triggers
    ):
        triggers.append("ambiguous-append-target")

    if (
        len(proposal.draft_topics) >= COMMONPLACE_CONFIG.ambiguous_topic_threshold
        and "broad-topic-spread" in enabled_triggers
    ):
        triggers.append("broad-topic-spread")

    return triggers


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
    "_collect_escalation_triggers",
    "_should_escalate",
    "build_user_prompt",
    "propose_entry",
]

"""Reusable Commonplace service helpers."""

from datetime import datetime, timezone
from typing import Dict

from .extractor import DEFAULT_MODEL, extract_session
from .markdown import render_markdown


def generate_wiki_markdown(
    transcript: str,
    session_type: str,
    title_hint: str = "",
    transcript_source: str = "api",
) -> Dict[str, str]:
    extracted = extract_session(
        transcript=transcript,
        session_type=session_type,
        title_hint=title_hint,
    )
    generated_at = datetime.now(timezone.utc)
    title = extracted["title"]
    model = extracted.get("_model", DEFAULT_MODEL)
    markdown = render_markdown(
        data=extracted,
        session_type=session_type,
        transcript_path=transcript_source,
        model=model,
        generated_at=generated_at,
    )
    return {
        "markdown": markdown,
        "title": title,
        "generated_at": generated_at.isoformat(),
        "model": model,
    }

"""Rendering helpers for formatting proposals as inbox-ready markdown."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .prompts import Proposal


@dataclass(frozen=True)
class SourceMetadata:
    """Minimal source metadata needed when rendering an inbox proposal."""

    filename: str
    ingested_at: datetime
    message: str | None = None
    display_path: str | None = None


def render_inbox_markdown(proposal: Proposal, source: SourceMetadata) -> str:
    """Render a validated proposal into inbox markdown with YAML front-matter."""
    lines = [
        "---",
        "proposal:",
        f"  action: {_string_value(proposal.action)}",
    ]

    if proposal.target_entry:
        lines.append(f'  target_entry: "{_escape_yaml_string(proposal.target_entry)}"')

    lines.extend(
        [
            "  reasoning: |",
            *_indent_block(proposal.reasoning, spaces=4),
            f"  confidence: {_string_value(proposal.confidence)}",
            "source:",
            f'  file: "{_escape_yaml_string(source.filename)}"',
        ]
    )

    if source.display_path:
        lines.append(f'  path: "{_escape_yaml_string(source.display_path)}"')

    lines.append(f"  ingested-at: {source.ingested_at.isoformat()}")

    if source.message:
        lines.append(f'  message: "{_escape_yaml_string(source.message)}"')

    body = proposal.draft_content.rstrip("\n")
    front_matter = "\n".join(lines)
    return f"{front_matter}\n---\n\n{body}\n"


def suggest_inbox_filename(
    proposal: Proposal,
    for_date: date,
    fallback_stem: str = "proposal",
) -> str:
    """Suggest a stable inbox filename using the date and proposal title."""
    base_text = proposal.draft_title or fallback_stem
    slug = _slugify(base_text) or "proposal"
    return f"{for_date.isoformat()}-{slug}.md"


def _slugify(value: str) -> str:
    """Convert a title-like string into a readable filename slug."""
    normalized = value.lower()
    normalized = re.sub(r"[^\w\s-]", "", normalized)
    normalized = re.sub(r"[-\s]+", "-", normalized)
    return normalized.strip("-_")


def _indent_block(value: str, spaces: int) -> list[str]:
    """Indent a multi-line block for YAML literal content."""
    prefix = " " * spaces
    block_lines = value.strip().splitlines() or [""]
    return [f"{prefix}{line}" if line else prefix for line in block_lines]


def _string_value(value: object) -> str:
    """Return the enum value when present, otherwise the string form."""
    return str(getattr(value, "value", value))


def _escape_yaml_string(value: str) -> str:
    """Escape double quotes for simple quoted YAML scalars."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


__all__ = ["SourceMetadata", "render_inbox_markdown", "suggest_inbox_filename"]

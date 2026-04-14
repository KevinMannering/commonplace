"""Markdown rendering for wiki pages."""

from datetime import datetime, timezone
from typing import Dict, Iterable, List


def concept_links(concepts: Iterable[Dict[str, str]]) -> str:
    names = [item["name"].strip() for item in concepts if item.get("name", "").strip()]
    return ", ".join(f"[[{name}]]" for name in names)


def _section(title: str, items: List[Dict[str, str]], fields: List[str]) -> str:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("_None captured._")
        lines.append("")
        return "\n".join(lines)

    for item in items:
        primary = item.get(fields[0], "").strip()
        lines.append(f"### {primary or 'Untitled'}")
        for field in fields[1:]:
            value = item.get(field, "").strip()
            if value:
                label = field.replace("_", " ").capitalize()
                lines.append(f"**{label}:** {value}")
        lines.append("")
    return "\n".join(lines)


def render_markdown(
    data: Dict[str, object],
    session_type: str,
    transcript_path: str,
    model: str,
    generated_at: datetime = None,
) -> str:
    generated_at = generated_at or datetime.now(timezone.utc)
    links = concept_links(data.get("named_concepts", []))

    lines = [
        "---",
        f"title: {data['title']}",
        f"session_type: {session_type}",
        f"generated_at: {generated_at.isoformat()}",
        f"source_transcript: {transcript_path}",
        f"model: {model}",
        "---",
        "",
        f"# {data['title']}",
        "",
        "## Summary",
        "",
        str(data["summary"]).strip(),
        "",
    ]

    if links:
        lines.extend(["## Concept Links", "", links, ""])

    if session_type == "strategy":
        lines.extend(
            [
                _section("Key Decisions", data.get("decisions", []), ["decision", "reasoning"]),
                _section("Assumptions", data.get("assumptions", []), ["assumption", "reasoning"]),
                _section("Challenges", data.get("challenges", []), ["challenge", "why_it_matters"]),
                _section("Open Questions", data.get("open_questions", []), ["question", "why_open"]),
            ]
        )
    else:
        lines.extend(
            [
                _section("Claims", data.get("claims", []), ["claim", "reasoning"]),
                _section("Evidence", data.get("evidence", []), ["point", "supports"]),
                _section("Sources", data.get("sources", []), ["source", "relevance"]),
                _section("Gaps", data.get("gaps", []), ["gap", "why_it_matters"]),
                _section("Conclusions", data.get("conclusions", []), ["conclusion", "basis"]),
            ]
        )

    lines.extend(
        [
            _section("Pivots", data.get("pivots", []), ["from_position", "to_position", "why_it_changed"]),
            _section("Named Concepts", data.get("named_concepts", []), ["name", "description"]),
        ]
    )

    return "\n".join(lines).strip() + "\n"

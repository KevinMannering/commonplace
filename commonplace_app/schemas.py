"""Extraction schemas and prompts for Commonplace."""

from typing import Dict, List


SYSTEM_PROMPT = """You are Commonplace, a careful editorial assistant.

Your job is to read a conversation transcript and convert it into a structured record for a personal wiki.

Rules:
- Capture only what is actually supported by the transcript.
- Prefer concise, high-signal phrasing.
- Preserve uncertainty instead of inventing certainty.
- When reasoning is present, summarize the reasoning clearly.
- Named concepts and frameworks should be normalized into short reusable names.
- Always call the provided function with valid JSON.
"""


def _shared_properties() -> Dict[str, object]:
    return {
        "title": {
            "type": "string",
            "description": "A concise page title for the session.",
        },
        "summary": {
            "type": "string",
            "description": "A short summary of the most important thinking from the session.",
        },
        "pivots": {
            "type": "array",
            "description": "Moments where the thinking changed and why.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "from_position": {"type": "string"},
                    "to_position": {"type": "string"},
                    "why_it_changed": {"type": "string"},
                },
                "required": ["from_position", "to_position", "why_it_changed"],
            },
        },
        "named_concepts": {
            "type": "array",
            "description": "Named ideas, frameworks, or concepts worth preserving as reusable wiki references.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["name", "description"],
            },
        },
    }


def strategy_tool() -> Dict[str, object]:
    properties = _shared_properties()
    properties.update(
        {
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "decision": {"type": "string"},
                        "reasoning": {"type": "string"},
                    },
                    "required": ["decision", "reasoning"],
                },
            },
            "assumptions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "assumption": {"type": "string"},
                        "reasoning": {"type": "string"},
                    },
                    "required": ["assumption", "reasoning"],
                },
            },
            "challenges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "challenge": {"type": "string"},
                        "why_it_matters": {"type": "string"},
                    },
                    "required": ["challenge", "why_it_matters"],
                },
            },
            "open_questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "question": {"type": "string"},
                        "why_open": {"type": "string"},
                    },
                    "required": ["question", "why_open"],
                },
            },
        }
    )
    return {
        "type": "function",
        "name": "capture_strategy_session",
        "description": "Capture a strategy conversation into a structured wiki-ready record.",
        "strict": True,
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": [
                "title",
                "summary",
                "decisions",
                "assumptions",
                "challenges",
                "open_questions",
                "pivots",
                "named_concepts",
            ],
        },
    }


def research_tool() -> Dict[str, object]:
    properties = _shared_properties()
    properties.update(
        {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "claim": {"type": "string"},
                        "reasoning": {"type": "string"},
                    },
                    "required": ["claim", "reasoning"],
                },
            },
            "evidence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "point": {"type": "string"},
                        "supports": {"type": "string"},
                    },
                    "required": ["point", "supports"],
                },
            },
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "source": {"type": "string"},
                        "relevance": {"type": "string"},
                    },
                    "required": ["source", "relevance"],
                },
            },
            "gaps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "gap": {"type": "string"},
                        "why_it_matters": {"type": "string"},
                    },
                    "required": ["gap", "why_it_matters"],
                },
            },
            "conclusions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "conclusion": {"type": "string"},
                        "basis": {"type": "string"},
                    },
                    "required": ["conclusion", "basis"],
                },
            },
        }
    )
    return {
        "type": "function",
        "name": "capture_research_session",
        "description": "Capture a research conversation into a structured wiki-ready record.",
        "strict": True,
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": [
                "title",
                "summary",
                "claims",
                "evidence",
                "sources",
                "gaps",
                "conclusions",
                "pivots",
                "named_concepts",
            ],
        },
    }


def strategy_response_format() -> Dict[str, object]:
    tool = strategy_tool()
    return {
        "type": "json_schema",
        "name": tool["name"],
        "strict": True,
        "schema": tool["parameters"],
    }


def research_response_format() -> Dict[str, object]:
    tool = research_tool()
    return {
        "type": "json_schema",
        "name": tool["name"],
        "strict": True,
        "schema": tool["parameters"],
    }


def build_messages(session_type: str, transcript: str, title_hint: str = "") -> List[Dict[str, object]]:
    title_line = f"Title hint: {title_hint}\n" if title_hint else ""
    session_prompt = {
        "strategy": """Session type: strategy

Capture:
- key decisions made
- assumptions in play
- core challenges
- open questions
- pivots in the thinking
- named concepts or frameworks

Focus on positions taken and the reasoning behind them.
""",
        "research": """Session type: research

Capture:
- claims made
- evidence discussed
- sources cited or implied
- gaps in the research
- conclusions reached
- pivots in the thinking
- named concepts or frameworks

Focus on what the session concluded, what supports those conclusions, and what remains unresolved.
""",
    }[session_type]

    return [
        {
            "role": "system",
            "content": [
                {
                    "type": "input_text",
                    "text": SYSTEM_PROMPT,
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"""{session_prompt}
{title_line}
Transcript:
{transcript}
""",
                }
            ],
        },
    ]

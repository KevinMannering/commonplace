"""OpenAI-backed extraction for Commonplace."""

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict

from .schemas import (
    build_messages,
    research_response_format,
    strategy_response_format,
)


API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_MAX_OUTPUT_TOKENS = 2200
RETRY_MAX_OUTPUT_TOKENS = 5000


class ExtractionError(RuntimeError):
    """Raised when extraction fails."""


def extract_session(transcript: str, session_type: str, title_hint: str = "") -> Dict[str, object]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ExtractionError("OPENAI_API_KEY is not set.")

    model = os.environ.get("COMMONPLACE_MODEL", DEFAULT_MODEL)
    response_format = strategy_response_format() if session_type == "strategy" else research_response_format()

    body = _create_response(
        api_key=api_key,
        model=model,
        session_type=session_type,
        response_format=response_format,
        transcript=transcript,
        title_hint=title_hint,
        max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
    )

    if _needs_retry_for_truncation(body):
        body = _create_response(
            api_key=api_key,
            model=model,
            session_type=session_type,
            response_format=response_format,
            transcript=transcript,
            title_hint=title_hint,
            max_output_tokens=RETRY_MAX_OUTPUT_TOKENS,
        )

    data = _extract_structured_data(body)
    if not data:
        debug_path = _maybe_write_debug_body(body)
        details = _describe_unparseable_response(body)
        suffix = f" Raw response saved to {debug_path}." if debug_path else ""
        raise ExtractionError(f"Model did not return parseable structured JSON. {details}{suffix}".strip())

    data["_model"] = body.get("model", model)
    data["_response_id"] = body.get("id", "")
    return data


def _create_response(
    api_key: str,
    model: str,
    session_type: str,
    response_format: Dict[str, object],
    transcript: str,
    title_hint: str,
    max_output_tokens: int,
) -> Dict[str, object]:
    payload = {
        "model": model,
        "input": build_messages(session_type=session_type, transcript=transcript, title_hint=title_hint),
        "store": False,
        "reasoning": {"effort": "low"},
        "max_output_tokens": max_output_tokens,
        "text": {
            "format": response_format,
            "verbosity": "low",
        },
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise ExtractionError(f"OpenAI API request failed: {exc.code} {message}") from exc
    except urllib.error.URLError as exc:
        raise ExtractionError(f"Network error while calling OpenAI: {exc}") from exc


def _find_function_call(body: Dict[str, object]) -> Dict[str, object]:
    for item in body.get("output", []):
        if item.get("type") == "function_call":
            return item
    return {}


def _extract_structured_data(body: Dict[str, object]) -> Dict[str, object]:
    parsed = _extract_from_output_items(body)
    if parsed:
        return parsed

    top_level_output_text = body.get("output_text")
    if isinstance(top_level_output_text, str):
        parsed_text = _load_json_loose(top_level_output_text)
        if parsed_text:
            return parsed_text

    function_call = _find_function_call(body)
    if function_call:
        try:
            return json.loads(function_call["arguments"])
        except (KeyError, json.JSONDecodeError):
            pass

    return {}


def _extract_from_output_items(body: Dict[str, object]) -> Dict[str, object]:
    for item in body.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "refusal":
                raise ExtractionError(f"Model refused extraction: {content.get('refusal', 'Unknown refusal')}")

            parsed = content.get("parsed")
            if isinstance(parsed, dict):
                return parsed

            text_value = content.get("text")
            if isinstance(text_value, str):
                parsed_text = _load_json_loose(text_value)
                if parsed_text:
                    return parsed_text
    return {}


def _load_json_loose(text: str) -> Dict[str, object]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)

    try:
        value = json.loads(stripped)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if not match:
        return {}

    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def _describe_unparseable_response(body: Dict[str, object]) -> str:
    parts = []

    status = body.get("status")
    if status:
        parts.append(f"status={status}")

    incomplete = body.get("incomplete_details")
    if incomplete:
        parts.append(f"incomplete_details={json.dumps(incomplete)}")

    error = body.get("error")
    if error:
        parts.append(f"error={json.dumps(error)}")

    snippet = _extract_text_snippet(body)
    if snippet:
        parts.append(f"first_text={snippet!r}")

    return "; ".join(parts) if parts else "No additional response details were available."


def _extract_text_snippet(body: Dict[str, object]) -> str:
    top_level_output_text = body.get("output_text")
    if isinstance(top_level_output_text, str) and top_level_output_text.strip():
        return top_level_output_text.strip()[:300]

    for item in body.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "refusal":
                refusal = content.get("refusal")
                if isinstance(refusal, str):
                    return refusal[:300]
            text_value = content.get("text")
            if isinstance(text_value, str) and text_value.strip():
                return text_value.strip()[:300]
    return ""


def _maybe_write_debug_body(body: Dict[str, object]) -> str:
    if not os.environ.get("COMMONPLACE_DEBUG"):
        return ""

    debug_dir = Path(os.environ.get("COMMONPLACE_DEBUG_DIR", "debug"))
    debug_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = debug_dir / f"openai-response-{timestamp}.json"
    path.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return str(path)


def _needs_retry_for_truncation(body: Dict[str, object]) -> bool:
    incomplete = body.get("incomplete_details")
    if not isinstance(incomplete, dict):
        return False
    return incomplete.get("reason") == "max_output_tokens"

"""Input loading for local transcripts and shared chat URLs."""

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple


USER_AGENT = "Commonplace/0.1 (+https://commonplace.local)"
ROLE_ALIASES = {
    "human": "User",
    "user": "User",
    "assistant": "Assistant",
    "ai": "Assistant",
    "model": "Assistant",
    "system": "System",
}


@dataclass
class LoadedInput:
    transcript: str
    source_label: str
    title_hint: str = ""


class InputError(RuntimeError):
    """Raised when input cannot be loaded."""


class ShareHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_script = False
        self.in_style = False
        self.capture_title = False
        self.title = ""
        self.text_parts: List[str] = []
        self.script_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == "script":
            self.in_script = True
        elif tag == "style":
            self.in_style = True
        elif tag == "title":
            self.capture_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.in_script = False
        elif tag == "style":
            self.in_style = False
        elif tag == "title":
            self.capture_title = False

    def handle_data(self, data: str) -> None:
        if self.capture_title:
            self.title += data
        if self.in_script:
            self.script_parts.append(data)
            return
        if self.in_style:
            return
        cleaned = data.strip()
        if cleaned:
            self.text_parts.append(cleaned)


def is_url(value: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def load_input(input_arg: str) -> LoadedInput:
    if not input_arg or input_arg == "-":
        transcript = sys.stdin.read().strip()
        return LoadedInput(transcript=transcript, source_label="stdin")

    if is_url(input_arg):
        transcript, title_hint = fetch_shared_transcript(input_arg)
        return LoadedInput(transcript=transcript, source_label=input_arg, title_hint=title_hint)

    path = Path(input_arg)
    return LoadedInput(transcript=path.read_text(encoding="utf-8").strip(), source_label=str(path))


def fetch_shared_transcript(url: str) -> Tuple[str, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc == "claude.ai":
        api_result = fetch_claude_snapshot(url)
        if api_result:
            return api_result

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            html = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise InputError(f"Could not load shared chat URL: {exc.code} {message}") from exc
    except urllib.error.URLError as exc:
        raise InputError(f"Network error while loading shared chat URL: {exc}") from exc

    transcript, title_hint = extract_transcript_from_html(html, url)
    if not transcript:
        raise InputError("Shared chat page loaded, but no transcript content could be extracted.")
    return transcript, title_hint


def fetch_claude_snapshot(url: str) -> Optional[Tuple[str, str]]:
    share_id = extract_share_id(url)
    if not share_id:
        return None

    snapshot_url = f"https://claude.ai/api/chat_snapshots/{share_id}?rendering_mode=messages&render_all_tools=true"
    request = urllib.request.Request(snapshot_url, headers={"User-Agent": USER_AGENT}, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
        return None

    transcript = extract_claude_snapshot_messages(payload)
    if not transcript:
        return None

    title_hint = clean_text(str(payload.get("name") or payload.get("title") or ""))
    return transcript, title_hint


def extract_share_id(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "share":
        return parts[1]
    return ""


def extract_transcript_from_html(html: str, url: str) -> Tuple[str, str]:
    parser = ShareHTMLParser()
    parser.feed(html)

    title_hint = clean_text(parser.title)
    structured = extract_structured_messages(parser.script_parts)
    if structured:
        return structured, title_hint

    fallback = fallback_visible_text(parser.text_parts, url)
    return fallback, title_hint


def extract_structured_messages(script_parts: List[str]) -> str:
    transcripts: List[str] = []
    seen = set()

    for script in script_parts:
        candidates = extract_json_candidates(script)
        for candidate in candidates:
            messages = collect_messages(candidate)
            if len(messages) < 2:
                continue
            key = tuple(messages)
            if key in seen:
                continue
            seen.add(key)
            transcripts.extend(messages)

    if not transcripts:
        return ""

    deduped: List[str] = []
    last = None
    for line in transcripts:
        if line != last:
            deduped.append(line)
        last = line
    return "\n\n".join(deduped).strip()


def extract_json_candidates(script: str) -> List[object]:
    candidates: List[object] = []
    stripped = script.strip()
    if not stripped:
        return candidates

    if stripped.startswith("{") or stripped.startswith("["):
        parsed = try_parse_json(stripped)
        if parsed is not None:
            candidates.append(parsed)

    for match in re.finditer(r"(\{.*\}|\[.*\])", stripped, flags=re.DOTALL):
        parsed = try_parse_json(match.group(1))
        if parsed is not None:
            candidates.append(parsed)

    return candidates


def try_parse_json(candidate: str):
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def collect_messages(payload: object) -> List[str]:
    messages: List[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            maybe = message_from_dict(node)
            if maybe:
                messages.append(maybe)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return messages


def extract_claude_snapshot_messages(payload: Dict[str, object]) -> str:
    raw_messages = payload.get("chat_messages")
    if not isinstance(raw_messages, list):
        return ""

    sorted_messages = sorted(
        [item for item in raw_messages if isinstance(item, dict)],
        key=lambda item: item.get("index", 0),
    )
    lines: List[str] = []
    for item in sorted_messages:
        sender = item.get("sender")
        if not isinstance(sender, str):
            continue
        role = ROLE_ALIASES.get(sender.lower(), sender.title())
        text = extract_text(item)
        if text:
            lines.append(f"{role}: {text}")
    return "\n\n".join(lines).strip()


def message_from_dict(node: Dict[str, object]) -> str:
    role = extract_role(node)
    text = extract_text(node)
    if not role or not text:
        return ""
    return f"{role}: {text}"


def extract_role(node: Dict[str, object]) -> str:
    raw_role = node.get("role")
    if isinstance(raw_role, str):
        return ROLE_ALIASES.get(raw_role.lower(), raw_role.title())

    author = node.get("author")
    if isinstance(author, dict):
        for key in ("role", "name"):
            value = author.get(key)
            if isinstance(value, str):
                return ROLE_ALIASES.get(value.lower(), value.title())

    sender = node.get("sender")
    if isinstance(sender, str):
        return ROLE_ALIASES.get(sender.lower(), sender.title())

    return ""


def extract_text(node: Dict[str, object]) -> str:
    for key in ("text", "content", "message", "body", "markdown", "value"):
        if key in node:
            text = flatten_content(node[key])
            if text:
                return text

    if isinstance(node.get("content"), dict):
        for key in ("parts", "text"):
            if key in node["content"]:
                text = flatten_content(node["content"][key])
                if text:
                    return text

    return ""


def flatten_content(value: object) -> str:
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        parts = [flatten_content(item) for item in value]
        return clean_text("\n".join(part for part in parts if part))
    if isinstance(value, dict):
        for key in ("text", "value", "content", "parts", "body", "markdown"):
            if key in value:
                text = flatten_content(value[key])
                if text:
                    return text
    return ""


def fallback_visible_text(text_parts: List[str], url: str) -> str:
    filtered: List[str] = []
    seen = set()

    for part in text_parts:
        cleaned = clean_text(part)
        if not cleaned:
            continue
        if len(cleaned) < 2:
            continue
        if cleaned.lower() in {"share", "copy link", "chatgpt", "claude"}:
            continue
        if cleaned in seen:
            continue
        seen.add(cleaned)
        filtered.append(cleaned)

    domain = urllib.parse.urlparse(url).netloc
    header = f"Source: {domain}"
    body = "\n\n".join(filtered)
    return f"{header}\n\n{body}".strip()


def clean_text(text: str) -> str:
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

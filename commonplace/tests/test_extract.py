"""Tests for source extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from commonplace.extract import extract_text


def test_extract_markdown_file_returns_expected_text(tmp_path: Path) -> None:
    source_path = tmp_path / "note.md"
    source_path.write_text("# Title\n\nBody text.\n", encoding="utf-8")

    extracted = extract_text(source_path)

    assert extracted.source_type == "markdown"
    assert extracted.filename == "note.md"
    assert extracted.extension == ".md"
    assert extracted.content_text == "# Title\n\nBody text."


def test_extract_plain_text_file_returns_expected_text(tmp_path: Path) -> None:
    source_path = tmp_path / "note.txt"
    source_path.write_text("Plain text source.\n", encoding="utf-8")

    extracted = extract_text(source_path)

    assert extracted.source_type == "text"
    assert extracted.filename == "note.txt"
    assert extracted.extension == ".txt"
    assert extracted.content_text == "Plain text source."


def test_extract_unsupported_extension_raises_value_error(tmp_path: Path) -> None:
    source_path = tmp_path / "note.rtf"
    source_path.write_text("Unsupported", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported source type"):
        extract_text(source_path)


def test_extract_missing_file_raises_file_not_found_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.md"

    with pytest.raises(FileNotFoundError, match="Source file does not exist"):
        extract_text(missing_path)

"""Extraction helpers for reading supported source files into normalized text."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractedSource:
    """Normalized source content plus lightweight file metadata."""

    path: Path
    source_type: str
    content_text: str
    filename: str
    extension: str
    page_count: int | None = None


def extract_text(path: Path) -> ExtractedSource:
    """Extract normalized text from a supported source file."""
    if not path.exists():
        raise FileNotFoundError(f"Source file does not exist: {path}")

    extension = path.suffix.lower()

    if extension == ".md":
        return _extract_markdown(path)
    if extension == ".txt":
        return _extract_plain_text(path)
    if extension == ".pdf":
        return _extract_pdf(path)

    raise ValueError(f"Unsupported source type: {extension or '<no extension>'}")


def _extract_markdown(path: Path) -> ExtractedSource:
    """Read a markdown source file as UTF-8 text."""
    return _build_text_source(path=path, source_type="markdown")


def _extract_plain_text(path: Path) -> ExtractedSource:
    """Read a plain text source file as UTF-8 text."""
    return _build_text_source(path=path, source_type="text")


def _build_text_source(path: Path, source_type: str) -> ExtractedSource:
    """Create a normalized extracted source from a UTF-8 text file."""
    content_text = path.read_text(encoding="utf-8").rstrip()

    return ExtractedSource(
        path=path,
        source_type=source_type,
        content_text=content_text,
        filename=path.name,
        extension=path.suffix.lower(),
        page_count=None,
    )


def _extract_pdf(path: Path) -> ExtractedSource:
    """Extract text from a PDF using pypdf without OCR."""
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "PDF extraction requires the 'pypdf' package to be installed."
        ) from exc

    reader = PdfReader(str(path))
    page_texts: list[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        cleaned_text = page_text.strip()
        if cleaned_text:
            page_texts.append(cleaned_text)

    content_text = "\n\n".join(page_texts).rstrip()

    if not content_text:
        raise ValueError(
            "PDF extraction produced no text. The PDF may be image-based, "
            "scanner-derived, or otherwise non-extractable without OCR."
        )

    return ExtractedSource(
        path=path,
        source_type="pdf",
        content_text=content_text,
        filename=path.name,
        extension=path.suffix.lower(),
        page_count=len(reader.pages),
    )

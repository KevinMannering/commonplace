"""FastAPI server for Commonplace extraction."""

import os
from typing import Literal, Optional

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel

from commonplace_app.extractor import ExtractionError
from commonplace_app.service import generate_wiki_markdown


app = FastAPI(title="Commonplace API", version="0.1.0")


class ExtractRequest(BaseModel):
    transcript: str
    session_type: Literal["strategy", "research"]
    title: Optional[str] = ""


class ExtractResponse(BaseModel):
    markdown: str
    title: str
    generated_at: str


def _require_api_key(api_key: Optional[str]) -> None:
    expected = os.environ.get("COMMONPLACE_SERVER_API_KEY")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="COMMONPLACE_SERVER_API_KEY is not configured on the server.",
        )
    if api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )


@app.post("/extract", response_model=ExtractResponse)
def extract_markdown(payload: ExtractRequest, x_api_key: Optional[str] = Header(default=None)) -> ExtractResponse:
    _require_api_key(x_api_key)

    if not payload.transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript must not be empty.",
        )

    try:
        result = generate_wiki_markdown(
            transcript=payload.transcript,
            session_type=payload.session_type,
            title_hint=payload.title or "",
            transcript_source="browser-extension",
        )
    except ExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return ExtractResponse(
        markdown=result["markdown"],
        title=result["title"],
        generated_at=result["generated_at"],
    )

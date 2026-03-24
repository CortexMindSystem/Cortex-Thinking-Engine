"""
Summary Ingestion API — ingest user-written markdown into CortexOS.

Accepts raw markdown text (summaries, analyses, notes) and creates
structured Items + KnowledgeNotes that feed into the full context layer.

This is how your thinking becomes part of the system.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from cortex_core.api.server import get_engine

router = APIRouter(prefix="/ingest", tags=["ingest"])


# ── Request / Response models ────────────────────────────────


class SummaryIngest(BaseModel):
    content: str
    source: str = ""
    tags: list[str] = Field(default_factory=list)
    create_notes: bool = True


class IngestResult(BaseModel):
    items_ingested: int
    notes_created: int


# ── Endpoints ────────────────────────────────────────────────


@router.post("/summary", response_model=IngestResult, status_code=201)
async def ingest_summary(body: SummaryIngest) -> dict:
    """Ingest a user-written markdown summary.

    Parses the markdown into sections, creates Items (raw data)
    and optionally KnowledgeNotes (structured insights).
    Content flows into scoring, signals, and focus briefs.
    """
    engine = get_engine()
    result = engine.ingest_summary(
        body.content,
        source=body.source,
        tags=body.tags,
        create_notes=body.create_notes,
    )
    return result

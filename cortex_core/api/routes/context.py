"""
Agent Context API routes — CortexOS as infrastructure for AI agents.

These endpoints expose memory, decisions, and priorities through
a clean interface that agents can query to gain awareness of the
user's situation.

Methods:
  GET  /context/goals        → active goals
  GET  /context/projects/:id → per-project context
  GET  /context/decisions    → recent decisions
  GET  /context/priorities   → today's priority brief
  GET  /context/signals      → emerging signals
  GET  /context/memory       → full memory state
  POST /context/insight      → store a new insight
  POST /context/decision     → record a decision
  POST /context/outcome      → record decision outcome
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from cortex_core.api.server import get_engine

router = APIRouter(prefix="/context", tags=["context"])


# ── Request/Response models ──────────────────────────────────


class InsightCreate(BaseModel):
    title: str
    summary: str = ""
    why_it_matters: str = ""
    architectural_implication: str = ""
    next_action: str = ""
    confidence: float = 0.5
    tags: list[str] = Field(default_factory=list)
    related_project: str = ""


class DecisionCreate(BaseModel):
    decision: str
    reason: str
    project: str = ""
    assumptions: list[str] = Field(default_factory=list)


class OutcomeCreate(BaseModel):
    decision_id: str
    outcome: str
    impact_score: float = 0.0


class RetrieveRequest(BaseModel):
    query: str
    source_type: str | None = None
    tags: list[str] | None = None
    max_results: int = 10


# ── Endpoints ────────────────────────────────────────────────


@router.get("/goals")
async def get_active_goals() -> list[str]:
    """Return the user's active goals."""
    engine = get_engine()
    return engine.get_active_goals()


@router.get("/projects/{project_name}")
async def get_project_context(project_name: str) -> dict:
    """Return full context for a specific project."""
    engine = get_engine()
    return engine.get_project_context(project_name)


@router.get("/decisions")
async def get_recent_decisions(limit: int = 10, project: str | None = None) -> list[dict]:
    """Return recent decisions, optionally by project."""
    engine = get_engine()
    return engine.get_decisions(project=project, limit=limit)


@router.get("/priorities")
async def get_priority_brief() -> dict:
    """Return today's priority brief."""
    engine = get_engine()
    brief = engine.get_priority_brief()
    if brief is None:
        raise HTTPException(status_code=404, detail="No priority brief generated yet.")
    return brief


@router.get("/signals")
async def get_signals() -> list[dict]:
    """Return current emerging signals."""
    engine = get_engine()
    return engine.get_signals()


@router.get("/insights")
async def get_insights(limit: int = 20) -> list[dict]:
    """Return recent structured insights."""
    engine = get_engine()
    return engine.get_insights(limit=limit)


@router.get("/memory")
async def get_full_context() -> dict:
    """Return the complete memory state for agent consumption."""
    engine = get_engine()
    return engine.get_full_context()


@router.post("/insight")
async def store_insight(body: InsightCreate) -> dict:
    """Store a new structured insight."""
    engine = get_engine()
    return engine.store_new_insight(**body.model_dump())


@router.post("/decision")
async def record_decision(body: DecisionCreate) -> dict:
    """Record a decision with full context."""
    engine = get_engine()
    return engine.record_decision(
        decision=body.decision,
        reason=body.reason,
        project=body.project,
        assumptions=body.assumptions,
    )


@router.post("/outcome")
async def record_outcome(body: OutcomeCreate) -> dict:
    """Record the outcome of a past decision (feedback loop)."""
    engine = get_engine()
    result = engine.record_outcome(body.decision_id, body.outcome, body.impact_score)
    if result is None:
        raise HTTPException(status_code=404, detail="Decision not found.")
    return result


@router.post("/retrieve")
async def retrieve(body: RetrieveRequest) -> list[dict]:
    """Hybrid retrieval across knowledge, insights, and items."""
    engine = get_engine()
    return engine.retrieve(
        body.query,
        source_type=body.source_type,
        tags=body.tags,
        max_results=body.max_results,
    )


# ── Feedback (UX loop) ──────────────────────────────────────


class FeedbackCreate(BaseModel):
    item: str
    useful: bool


@router.post("/feedback", status_code=204)
async def record_feedback(body: FeedbackCreate) -> None:
    """Record user feedback on a focus item (was this useful?)."""
    engine = get_engine()
    engine.record_feedback(item=body.item, useful=body.useful)

"""
Pydantic models for the CortexOS REST API.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ── Knowledge Notes ─────────────────────────────────────────────


class NoteCreate(BaseModel):
    title: str
    insight: str = ""
    implication: str = ""
    action: str = ""
    source_url: str = ""
    tags: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    title: str | None = None
    insight: str | None = None
    implication: str | None = None
    action: str | None = None
    source_url: str | None = None
    tags: list[str] | None = None
    archived: bool | None = None


class NoteResponse(BaseModel):
    id: str
    title: str
    insight: str
    implication: str
    action: str
    source_url: str
    tags: list[str]
    created_at: str
    updated_at: str
    archived: bool


# ── Posts ───────────────────────────────────────────────────────


class PostRequest(BaseModel):
    limit: int = 3
    platform: str = "general"
    use_llm: bool = False


class PostResponse(BaseModel):
    text: str
    platform: str
    note_id: str


# ── Pipeline ────────────────────────────────────────────────────


class PipelineRequest(BaseModel):
    use_llm: bool = False


class StepResultResponse(BaseModel):
    name: str
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    duration_s: float = 0.0
    error: str | None = None


class PipelineResponse(BaseModel):
    name: str
    started_at: str
    finished_at: str
    duration_s: float
    success: bool
    steps: list[StepResultResponse]


# ── Digest ──────────────────────────────────────────────────────


class DigestRequest(BaseModel):
    path: str | None = None
    use_llm: bool = False


# ── Health / Status ─────────────────────────────────────────────


class StatusResponse(BaseModel):
    version: str
    data_dir: str
    notes_count: int
    llm_provider: str
    llm_model: str


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: str


# ── Focus / Daily Brief ────────────────────────────────────────


class FocusItemResponse(BaseModel):
    rank: int
    title: str
    why_it_matters: str
    next_action: str
    source_url: str = ""
    relevance_score: float = 0.0
    tags: list[str] = Field(default_factory=list)


class DailyBriefResponse(BaseModel):
    date: str
    focus_items: list[FocusItemResponse]
    digest_quality: dict[str, Any] | None = None
    profile_summary: dict[str, Any] | None = None


class FocusRequest(BaseModel):
    digest_path: str | None = None
    use_llm: bool = False


# ── Profile ─────────────────────────────────────────────────────


class ProfileResponse(BaseModel):
    name: str = ""
    role: str = ""
    preferred_style: str = ""
    goals: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    current_projects: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    ignored_topics: list[str] = Field(default_factory=list)


class ProfileUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    preferred_style: str | None = None
    goals: list[str] | None = None
    interests: list[str] | None = None
    current_projects: list[str] | None = None
    constraints: list[str] | None = None
    ignored_topics: list[str] | None = None


# ── Digest Evaluation ──────────────────────────────────────────


class DigestEvalRequest(BaseModel):
    path: str | None = None
    context: list[str] | None = None


class ArticleScoreResponse(BaseModel):
    title: str
    score: float


class DigestEvalResponse(BaseModel):
    total_articles: int = 0
    ai_article_ratio: float = 0.0
    high_signal_ratio: float = 0.0
    signal_to_noise_ratio: float = 0.0
    context_keyword_coverage: float = 0.0
    project_fit_score: float = 0.0
    top_articles: list[ArticleScoreResponse] = Field(default_factory=list)


# ── Why Engine ────────────────────────────────────────────────────


class WhyEvaluateRequest(BaseModel):
    """Input for the Why Engine. Swift clients send this."""

    title: str
    content: str = ""
    source_type: str = "article"  # article, note, link, digest_item, project_update
    url: str = ""
    tags: list[str] = Field(default_factory=list)


class WhyEvaluateResponse(BaseModel):
    """Structured decision output. Swift clients decode this."""

    summary: str = ""
    why_it_matters: str = ""
    impact_on_active_project: str = ""
    contradiction_or_confirmation: str = ""  # supports, contradicts, unclear
    recommended_action: str = ""
    ignore_or_watch: str = ""  # act_now, watch, ignore
    confidence: float = 0.0
    tags: list[str] = Field(default_factory=list)
    evaluated_at: str = ""

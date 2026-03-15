"""
Focus routes — the primary CortexOS feature.
GET  /focus/today     → latest daily brief
POST /focus/generate  → generate a new focus brief
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from cortex_core.api.models import DailyBriefResponse, FocusRequest
from cortex_core.api.server import get_engine

router = APIRouter(prefix="/focus", tags=["focus"])


@router.get("/today", response_model=DailyBriefResponse)
async def get_today_brief():
    """Return the most recent focus brief."""
    engine = get_engine()
    brief = engine.get_latest_brief()
    if brief is None:
        raise HTTPException(status_code=404, detail="No focus brief generated yet. POST /focus/generate first.")
    return brief


@router.post("/generate", response_model=DailyBriefResponse)
async def generate_brief(body: FocusRequest):
    """Generate a new daily focus brief from the latest digest."""
    engine = get_engine()
    result = engine.generate_focus_brief(digest_path=body.digest_path, use_llm=body.use_llm)
    return result

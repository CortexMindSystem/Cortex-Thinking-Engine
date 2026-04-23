"""
Sync API route
--------------
GET /sync/snapshot — single-call pull of everything a Swift client needs.
POST /sync/newsletter/generate — generate latest newsletter draft on demand.

One endpoint. One model. Backend is source of truth.
Clients pull this on launch and on-demand refresh.
"""

from __future__ import annotations

from fastapi import APIRouter

from cortex_core.api.server import get_engine

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/snapshot")
async def get_snapshot() -> dict:
    """Return a single sync snapshot for Apple clients.

    Bundles profile, active project, priorities, recent decisions,
    insights, signals, and working memory into one response.
    """
    engine = get_engine()
    return engine.build_sync_snapshot()


@router.get("/today")
async def get_today_output() -> dict:
    """Return canonical SimpliXio Today output for sharing/automation."""
    engine = get_engine()
    return engine.build_today_output()


@router.post("/newsletter/generate")
async def generate_newsletter(payload: dict | None = None) -> dict:
    """Generate latest newsletter draft and return generation payload."""
    engine = get_engine()
    body = payload or {}
    period = str(body.get("period", "weekly")).strip() or "weekly"
    mode = str(body.get("mode", "weekly-lessons")).strip() or "weekly-lessons"
    strict_safety = bool(body.get("strict_safety", True))
    strict_taste = bool(body.get("strict_taste", True))
    return engine.generate_newsletter_draft(
        period=period,
        mode=mode,
        strict_safety=strict_safety,
        strict_taste=strict_taste,
    )

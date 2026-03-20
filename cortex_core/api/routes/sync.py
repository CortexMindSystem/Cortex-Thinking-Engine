"""
Sync API route
--------------
GET /sync/snapshot — single-call pull of everything a Swift client needs.

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

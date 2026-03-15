"""
Digest evaluation routes — quality scoring for weekly digests.
POST /digest/evaluate  → score a digest for relevance and quality
"""

from __future__ import annotations

from fastapi import APIRouter

from cortex_core.api.models import DigestEvalRequest, DigestEvalResponse
from cortex_core.api.server import get_engine

router = APIRouter(prefix="/digest", tags=["digest"])


@router.post("/evaluate", response_model=DigestEvalResponse)
async def evaluate_digest(body: DigestEvalRequest):
    """Evaluate the quality and relevance of a weekly digest."""
    engine = get_engine()
    result = engine.evaluate_digest(path=body.path, context=body.context)
    return result

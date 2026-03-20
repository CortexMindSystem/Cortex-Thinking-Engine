"""
Why Engine API route
---------------------
POST /why/evaluate — evaluate a single source item through the Why Engine.

Thin route. All intelligence lives in cortex_core/why_engine.py.
"""

from __future__ import annotations

from fastapi import APIRouter

from cortex_core.api.models import WhyEvaluateRequest, WhyEvaluateResponse
from cortex_core.api.server import get_engine

router = APIRouter(prefix="/why", tags=["why-engine"])


@router.post("/evaluate", response_model=WhyEvaluateResponse)
async def evaluate_item(request: WhyEvaluateRequest) -> WhyEvaluateResponse:
    """Evaluate a single source item and return a structured decision."""
    engine = get_engine()
    result = engine.evaluate_why(request.model_dump())
    return WhyEvaluateResponse(**result)

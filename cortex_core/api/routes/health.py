"""
Health & status endpoints.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from cortex_core.api.models import HealthResponse, StatusResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get("/status", response_model=StatusResponse)
async def status(engine=Depends(lambda: _get_engine())):
    return engine.status()


def _get_engine():
    from cortex_core.api.server import get_engine

    return get_engine()

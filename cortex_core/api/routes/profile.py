"""
Profile routes — user context for CortexOS recommendations.
GET   /profile       → current profile
PATCH /profile       → update profile fields
"""

from __future__ import annotations

from fastapi import APIRouter

from cortex_core.api.models import ProfileResponse, ProfileUpdate
from cortex_core.api.server import get_engine

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_model=ProfileResponse)
async def get_profile():
    """Return the current user profile."""
    engine = get_engine()
    return engine.get_profile()


@router.patch("/", response_model=ProfileResponse)
async def update_profile(body: ProfileUpdate):
    """Update profile fields. Only supplied fields are changed."""
    engine = get_engine()
    updates = body.model_dump(exclude_none=True)
    return engine.update_profile(**updates)

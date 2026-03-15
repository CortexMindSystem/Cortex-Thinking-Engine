"""
Social post generation endpoints.
"""

from fastapi import APIRouter, Depends

from cortex_core.api.models import PostRequest, PostResponse

router = APIRouter(prefix="/posts", tags=["Social Posts"])


def _engine():
    from cortex_core.api.server import get_engine

    return get_engine()


@router.post("/generate", response_model=list[PostResponse])
async def generate_posts(body: PostRequest, engine=Depends(_engine)):
    return engine.generate_posts(
        limit=body.limit,
        platform=body.platform,
        use_llm=body.use_llm,
    )


@router.post("/export")
async def export_posts(body: PostRequest, engine=Depends(_engine)):
    path = engine.export_posts(limit=body.limit, platform=body.platform)
    return {"exported_to": path}

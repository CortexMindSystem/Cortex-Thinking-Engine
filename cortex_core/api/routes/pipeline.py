"""
Pipeline execution endpoints.
"""

from fastapi import APIRouter, Depends

from cortex_core.api.models import DigestRequest, PipelineRequest, PipelineResponse

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


def _engine():
    from cortex_core.api.server import get_engine

    return get_engine()


@router.post("/run", response_model=PipelineResponse)
async def run_pipeline(body: PipelineRequest, engine=Depends(_engine)):
    result = engine.run_pipeline(use_llm=body.use_llm)
    return result


@router.post("/digest")
async def process_digest(body: DigestRequest, engine=Depends(_engine)):
    notes = engine.process_digest(path=body.path, use_llm=body.use_llm)
    return {"notes_created": len(notes), "notes": notes}


@router.get("/steps")
async def list_steps(engine=Depends(_engine)):
    pipe = engine.build_pipeline()
    return {"steps": pipe.step_names}

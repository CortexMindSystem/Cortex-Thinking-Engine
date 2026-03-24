"""
CortexOS API Server
--------------------
FastAPI application serving the CortexOS REST API.
Run directly: python -m cortex_core.api.server
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cortex_core.config import CortexConfig
from cortex_core.engine import CortexEngine

# ── Singleton engine ────────────────────────────────────────────

_engine: CortexEngine | None = None


def get_engine() -> CortexEngine:
    global _engine
    if _engine is None:
        _engine = CortexEngine(CortexConfig.load())
    return _engine


# ── Lifespan ────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_engine()  # warm up
    yield


# ── App factory ─────────────────────────────────────────────────


def create_app() -> FastAPI:
    app = FastAPI(
        title="CortexOS API",
        description="REST API for the CortexOS thinking engine",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS – allow iOS/macOS clients on any origin during development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from cortex_core.api.routes import context, digest, focus, health, ingest, knowledge, pipeline, posts, profile, sync, why

    app.include_router(health.router)
    app.include_router(focus.router)  # primary feature
    app.include_router(why.router)  # why engine — per-item intelligence
    app.include_router(sync.router)  # single-call sync for Apple clients
    app.include_router(ingest.router)  # user summary ingestion
    app.include_router(context.router)  # agent context API
    app.include_router(profile.router)
    app.include_router(knowledge.router)
    app.include_router(pipeline.router)
    app.include_router(posts.router)
    app.include_router(digest.router)

    return app


app = create_app()

# ── Direct execution ────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    config = CortexConfig.load()
    uvicorn.run(
        "cortex_core.api.server:app",
        host=config.api_host,
        port=config.api_port,
        reload=True,
    )

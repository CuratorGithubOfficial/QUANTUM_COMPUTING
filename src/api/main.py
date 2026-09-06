"""FastAPI приложение для квантовых экспериментов."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.job_store import InMemoryJobStore
from api.router import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    logger.info("Quantum Workspace API starting...")
    app.state.job_store = InMemoryJobStore()
    yield
    logger.info("Quantum Workspace API shutting down...")


def create_app() -> FastAPI:
    """Фабрика FastAPI-приложения."""
    app = FastAPI(
        title="Quantum Workspace API",
        description="API для квантовых экспериментов",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Роуты
    app.include_router(router)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health-check эндпоинт."""
        return {"status": "healthy"}

    return app


app = create_app()

"""
FastAPI application entry point for Aria Kitchen AI Restaurant Receptionist.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.settings import settings
from app.config.logging import logger
from app.db.database import engine, Base
from app.db import models  # noqa: F401 ensure all models are registered
from app.api.routes import health, restaurant, tables, conversation, tools
from app.api.websocket import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup & shutdown events.
    Ensures pgvector extension and database schema exist.
    """
    logger.info("app_starting", env=settings.app_env)
    try:
        async with engine.begin() as conn:
            # Enable pgvector if PostgreSQL is reachable
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info("db_initialized", status="success")
    except Exception as exc:
        logger.warn("db_initialization_deferred", reason=str(exc))

    yield

    logger.info("app_shutting_down")
    await engine.dispose()


app = FastAPI(
    title="Aria Kitchen — AI Restaurant Receptionist",
    description="Deterministic restaurant intelligence + LLM conversation engine",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS Middleware ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ─────────────────────────────────────────────────────────────────
# Root health endpoint
app.include_router(health.router)

# API prefixed endpoints
app.include_router(health.router, prefix="/api")
app.include_router(restaurant.router, prefix="/api")
app.include_router(tables.router, prefix="/api")
app.include_router(conversation.router, prefix="/api")
app.include_router(tools.router, prefix="/api")

# WebSocket router
app.include_router(ws_router)

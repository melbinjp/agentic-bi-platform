"""
FastAPI Application Entry Point

Mounts all routes, initialises the database on startup,
configures logging, and adds CORS middleware for the frontend.
"""

from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Monkey-patch chromadb telemetry to silence upstream signature errors in production
try:
    import chromadb.telemetry
    if hasattr(chromadb.telemetry, "Telemetry"):
        chromadb.telemetry.Telemetry.capture = lambda *args, **kwargs: None
except Exception:
    pass


from app.config import settings
from app.database import init_db
from app.observability import configure_logging
from app.api.routes import router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown logic."""
    configure_logging()
    logger.info("app_starting", env="development")
    await init_db()
    logger.info("database_initialised")
    yield
    logger.info("app_shutting_down")


app = FastAPI(
    title="Multi-Agent Business Intelligence Platform",
    description="Autonomous multi-agent system for business strategy generation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend to call the API
# Security: Restrict to only necessary methods and headers
# Wildcards with allow_credentials=True create security vulnerabilities
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:8501",
        "http://127.0.0.1:8501"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "Multi-Agent BI Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }

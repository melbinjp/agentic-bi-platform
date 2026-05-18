"""
Database Session Management

Provides async and sync database session factories for local Docker,
SQLite smoke tests, and managed Postgres deployments.
"""

import re

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base


def _strip_ssl_params(url: str) -> str:
    """Remove libpq-style SSL query params that asyncpg does not understand."""
    url = re.sub(r"[?&]sslmode=[^&]*", "", url)
    url = re.sub(r"[?&]channel_binding=[^&]*", "", url)
    url = url.replace("?&", "?")
    url = re.sub(r"\?$", "", url)
    url = re.sub(r"&$", "", url)
    return url


def _to_async_url(url: str) -> str:
    """Convert a plain Postgres URL from hosts such as Render to asyncpg."""
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    return url


def _to_sync_url(url: str) -> str:
    """Convert async URLs back to a psycopg2-compatible sync URL."""
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url[len("postgresql+asyncpg://") :]
    if url.startswith("sqlite+aiosqlite://"):
        return "sqlite://" + url[len("sqlite+aiosqlite://") :]
    return url


def _is_sqlite(url: str) -> bool:
    return make_url(url).drivername.startswith("sqlite")


def _is_postgres(url: str) -> bool:
    return make_url(url).drivername.startswith("postgresql")


def _ssl_required(url: str) -> bool:
    mode = (settings.database_ssl_mode or "disable").lower()
    if mode in {"require", "required", "true", "1", "yes"}:
        return True
    if mode in {"disable", "disabled", "false", "0", "no"}:
        return False
    try:
        parsed = make_url(url)
    except Exception:
        return False
    return parsed.query.get("sslmode") == "require"


_async_url = _strip_ssl_params(_to_async_url(settings.database_url))
_sync_url = _to_sync_url(settings.database_url_sync)

_async_engine_kwargs = {"echo": settings.app_env == "development"}
if _is_postgres(_async_url):
    _async_engine_kwargs.update({"pool_size": 20, "max_overflow": 10})
    if _ssl_required(settings.database_url):
        _async_engine_kwargs["connect_args"] = {"ssl": "require"}

_sync_engine_kwargs = {"echo": False}
if _is_postgres(_sync_url):
    _sync_engine_kwargs.update({"pool_size": 10, "max_overflow": 5})
    if _ssl_required(_sync_url):
        _sync_engine_kwargs["connect_args"] = {"sslmode": "require"}
elif _is_sqlite(_sync_url):
    _sync_engine_kwargs["connect_args"] = {"check_same_thread": False}


# --- Async Engine (for FastAPI) ---
async_engine = create_async_engine(
    _async_url,
    **_async_engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- Sync Engine (for Celery workers) ---
sync_engine = create_engine(
    _sync_url,
    **_sync_engine_kwargs,
)

SyncSessionLocal = sessionmaker(bind=sync_engine)


async def get_async_session():
    """FastAPI dependency for async DB sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Session:
    """Get a sync session for Celery workers. Caller must close."""
    return SyncSessionLocal()


async def init_db():
    """Create all tables. Called on app startup as a safe fallback."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

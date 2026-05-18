import os
import asyncio
import pytest

# 1. Force environment variables before any imports
db_path = os.path.abspath("test_agent_in.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{db_path}"
os.environ["APP_ENV"] = "testing"

# 2. Force settings singleton attributes
from app.config import settings
settings.database_url = f"sqlite+aiosqlite:///{db_path}"
settings.database_url_sync = f"sqlite:///{db_path}"
settings.app_env = "testing"

from app.database import init_db, async_engine, sync_engine
from app.models import Base

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Session fixture to set up and tear down test database files for testing."""
    # Synchronously create tables for the sync engine
    Base.metadata.create_all(bind=sync_engine)
    # Asynchronously create tables for the async engine
    await init_db()
    
    yield
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    Base.metadata.drop_all(bind=sync_engine)
    
    # Clean up the DB file safely
    try:
        if os.path.exists("test_agent_in.db"):
            os.remove("test_agent_in.db")
    except Exception:
        pass

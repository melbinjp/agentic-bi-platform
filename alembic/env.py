import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _to_sync_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url[len("postgresql+asyncpg://") :]
    if url.startswith("sqlite+aiosqlite://"):
        return "sqlite://" + url[len("sqlite+aiosqlite://") :]
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


def _database_url() -> str:
    sync_url = os.getenv("DATABASE_URL_SYNC")
    if sync_url:
        return _to_sync_url(sync_url)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return _to_sync_url(database_url)
    return "postgresql://postgres:postgres@localhost:5432/agent_in"


def run_migrations_offline() -> None:
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

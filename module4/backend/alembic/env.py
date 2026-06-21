"""
Alembic environment script for Module 4.

Reads DATABASE_URL from the environment (or .env file) at migration time
so credentials are never hardcoded. Supports both online (real Postgres)
and offline (SQL script generation) modes.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Put the module4 root on sys.path so "from models import ..." works ─────
_MODULE4_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_MODULE4_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULE4_ROOT))

# ── Import all ORM models so Alembic's autogenerate picks up every table ───
import module4.backend.models as models  # noqa: F401, E402  — registers all models on Base.metadata
from module4.backend.core.database import Base  # noqa: E402

# ── Alembic Config object ──────────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url from environment variable if set
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata object for autogenerate support
target_metadata = Base.metadata


MODULE_4_TABLES = {
    'audit_logs', 'ledger_events', 'complaints', 
    'security_alerts', 'trust_scores', 'hospital_metrics', 
    'emergency_overrides'
}

def include_name(name, type_, parent_names):
    if type_ == "table":
        return name in MODULE_4_TABLES
    return True

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This generates SQL statements without connecting to the DB.
    Useful for reviewing what alembic upgrade head will execute.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates a connection to the DB and runs migrations in a transaction.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

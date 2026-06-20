"""
Module 4 - Database session management.

Uses SQLAlchemy with Supabase Postgres. Exposes a `get_db` dependency
for FastAPI routes, plus the declarative `Base` used by all models.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from module4.backend.core.config import settings

# --- SQLite compatibility patch for postgresql.UUID ---
if settings.DATABASE_URL.startswith("sqlite"):
    import uuid as _uuid
    import sqlalchemy.dialects.postgresql as pg_dialect
    from sqlalchemy.types import TypeDecorator, CHAR

    class SQLiteUUID(TypeDecorator):
        impl = CHAR(36)
        cache_ok = True
        def process_bind_param(self, value, dialect):
            return str(value) if value else None
        def process_result_value(self, value, dialect):
            return _uuid.UUID(str(value)) if value else None

    class _CompatUUID:
        def __new__(cls, as_uuid=False):
            return SQLiteUUID()

    pg_dialect.UUID = _CompatUUID

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

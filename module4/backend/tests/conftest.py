"""
pytest fixtures for Module 4 test suite.

Every test gets a fresh in-memory SQLite database and an isolated
FastAPI TestClient — no shared state between tests.

Design decisions:
  - Uses SQLite for speed and zero external dependency.
  - UUID columns use a custom TypeDecorator so SQLite stores them as strings.
  - JWT tokens are minted locally with the test secret (CHANGE_ME_DEV_SECRET).
  - Each fixture is function-scoped (default), so tests are order-independent.
"""

import uuid
from datetime import datetime, timedelta

import pytest

# ── Override DATABASE_URL before importing any app modules ─────────────────
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "CHANGE_ME_DEV_SECRET"

# ── Patch SQLAlchemy's postgresql.UUID to be SQLite-compatible ─────────────
# The models use `postgresql.UUID(as_uuid=True)` which SQLite doesn't support.
# We replace it with a TypeDecorator that stores UUIDs as VARCHAR in SQLite.
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import sqlalchemy.dialects.postgresql as pg_dialect


class SQLiteUUID(TypeDecorator):
    """UUID type that works on both Postgres and SQLite."""
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(str(value))


# Monkey-patch postgresql.UUID so existing model files work under SQLite
_original_uuid = pg_dialect.UUID


class _CompatUUID:
    """Drop-in replacement for postgresql.UUID that renders as SQLiteUUID on SQLite."""
    def __new__(cls, as_uuid=False):
        return SQLiteUUID()


pg_dialect.UUID = _CompatUUID

# ── Now import app modules (after patching) ────────────────────────────────
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from module4.backend.core.config import settings
from module4.backend.core.database import Base, get_db
from module4.backend.main import app

SQLITE_URL = "sqlite:///:memory:"
TEST_SECRET = "CHANGE_ME_DEV_SECRET"
ALGORITHM = "HS256"


@pytest.fixture()
def db_engine():
    """Create a fresh SQLite engine and schema for one test."""
    engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    import module4.backend.models as models  # noqa: F401 — registers all ORM classes on Base
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """Yield a DB session for one test; rolled back after."""
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """
    TestClient wired to the isolated SQLite session.
    Overrides get_db for all routes.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def make_token(user_id: str, role: str, hospital_id: str | None = None) -> str:
    """Mint a HS256 JWT with the test secret."""
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    if hospital_id:
        payload["hospital_id"] = hospital_id
    return jose_jwt.encode(payload, TEST_SECRET, algorithm=ALGORITHM)


def auth(user_id: str, role: str, hospital_id: str | None = None) -> dict:
    """Return Authorization header dict for TestClient requests."""
    return {"Authorization": f"Bearer {make_token(user_id, role, hospital_id)}"}


# Convenient pre-built header fixtures
@pytest.fixture()
def patient_headers():
    return auth("patient-001", "patient")

@pytest.fixture()
def doctor_headers():
    return auth("doctor-001", "doctor")

@pytest.fixture()
def admin_headers():
    return auth("admin-001", "admin", "hospital-A")

@pytest.fixture()
def super_admin_headers():
    return auth("superadmin-001", "super_admin")

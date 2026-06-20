"""
Module 4 - Governance & Security Intelligence
FastAPI application entrypoint.

Run with:
    uvicorn main:app --reload --port 8004

Features:
  - Structured error responses: all errors returned as {"error": {"code": ..., "message": ...}}
  - Rate limiting via slowapi: POST /complaints (5/min), POST /emergency (10/min)
  - Deep health check: GET /health verifies DB connectivity (SELECT 1)
  - Structured JSON logging on every write operation
  - Immutable audit ledger (hash-chain) mirroring critical actions
"""

import json
import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from module4.backend.routes import alerts_routes, audit_routes, complaints_routes, emergency_routes, fraud_routes, hospital_risk_routes, ledger_routes
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text

from module4.backend.core.config import settings
from module4.backend.core.database import Base, SessionLocal, engine
from module4.backend.routes import (
    trust_score_routes,
)

# ---------------------------------------------------------------------------
# Logging — structured JSON output, one line per event
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # each log call already produces a JSON string
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter (slowapi)
# Rate limits (documented here as the security-relevant config):
#   POST /complaints : 5/minute per IP  — patient spamming is a fraud signal
#   POST /emergency  : 10/minute per IP — override spamming triggers fraud alert
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Governance, audit, fraud detection, and trust scoring for the "
        "Patient-Sovereign Prescription Intelligence Network."
    ),
    version="0.2.0",
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — open for hackathon demo; tighten before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Structured error handlers
# Replaces FastAPI's default {"detail": "..."} with {"error": {"code", "message"}}
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Convert HTTPException to structured error envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": str(exc.status_code), "message": exc.detail}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert Pydantic validation errors to structured error envelope."""
    messages = "; ".join(
        f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}" for e in exc.errors()
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "422", "message": messages}},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all: log and return 500 structured error."""
    logger.error(json.dumps({
        "action": "UNHANDLED_EXCEPTION",
        "path": str(request.url),
        "error": str(exc),
    }))
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "500", "message": "Internal server error"}},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(complaints_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(ledger_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(trust_score_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(emergency_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(hospital_risk_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(fraud_routes.router, prefix=settings.API_V1_PREFIX)


# ---------------------------------------------------------------------------
# Root + Health
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    """Module identification endpoint."""
    return {
        "module": "Module 4 - Governance & Security Intelligence",
        "status": "running",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
def health_check():
    """
    Deep health check.

    Verifies DB connectivity with a lightweight SELECT 1 query.
    Returns 200 + {"status": "ok", "db": "connected"} when healthy.
    Returns 503 + {"status": "degraded", "db": "unreachable", "error": "..."}
    when the database cannot be reached, so load balancers/orchestrators
    can route traffic away from an unhealthy instance.
    """
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as exc:
        logger.error(json.dumps({
            "action": "HEALTH_CHECK",
            "outcome": "db_unreachable",
            "error": str(exc),
        }))
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "db": "unreachable", "error": str(exc)},
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    """
    For local/dev convenience only. In production, use Alembic migrations
    instead of create_all(). Run: alembic upgrade head
    """
    if settings.ENVIRONMENT == "development":
        import module4.backend.models as models  # noqa: F401  (ensures all models are registered on Base)
        Base.metadata.create_all(bind=engine)

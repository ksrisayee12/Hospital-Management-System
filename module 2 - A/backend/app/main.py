"""
FastAPI Application Entry Point.
Module 2: Patient Healthcare Vault (Intelligence Layer).
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.dependencies import DatabaseManager
from app.utils.exceptions import HealthcareException, exception_to_http_exception
from app.routes import include_healthcare_routes, include_ai_routes
from app.services import ai_service


# Setup basic logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("healthcare_vault")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Patient Healthcare Vault (Module 2)")
    
    # Initialize Database
    DatabaseManager.initialize()
    from app.models import Base
    async with DatabaseManager._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database connection initialized and tables created")
    
    # Initialize AI Models (HuggingFace)
    try:
        # Load in background thread or just lazily. Here we call init which loads it.
        ai_service.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize AI service: {e}")
    
    yield
    
    # Shutdown events
    logger.info("Shutting down...")
    await DatabaseManager.close()


# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for custom exceptions
@app.exception_handler(HealthcareException)
async def healthcare_exception_handler(request: Request, exc: HealthcareException):
    http_exc = exception_to_http_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"success": False, "message": http_exc.detail}
    )


# Include all routers
include_healthcare_routes(app)
include_ai_routes(app)


@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "ai_backend": ai_service._active_model
    }

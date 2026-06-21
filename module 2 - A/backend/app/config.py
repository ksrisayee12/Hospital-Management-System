"""
Configuration module for healthcare vault backend.
Manages environment variables, database settings, and application config.
"""

import os
from functools import lru_cache
from typing import Optional, List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Application
    APP_NAME: str = "Patient-Sovereign Prescription Intelligence Network"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost:5432/healthcare_vault"
    )
    DATABASE_ECHO: bool = DEBUG
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # Security & Encryption
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AES-256 Encryption Key (32 bytes for AES-256)
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "dev-encryption-key-32-bytes-long!!")

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "your-supabase-key")
    SUPABASE_STORAGE_BUCKET: str = "health-vault"

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", SECRET_KEY)
    JWT_ALGORITHM: str = "HS256"

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    API_TITLE: str = APP_NAME
    API_DESCRIPTION: str = "Patient-owned healthcare vault with secure access control"
    API_VERSION: str = APP_VERSION
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000",
    ]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "json"  # 'json' or 'text'

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_EXTENSIONS: list = [
        "pdf", "jpg", "jpeg", "png", "gif",
        "doc", "docx", "xls", "xlsx", "csv", "dcm"
    ]

    # Wearable Data
    WEARABLE_BATCH_SIZE: int = 100
    WEARABLE_RETENTION_DAYS: int = 365

    # =========================================================================
    # AI / ML SETTINGS
    # =========================================================================

    # HuggingFace Models
    AI_BACKEND: str = os.getenv("AI_BACKEND", "huggingface")  # huggingface | ollama | auto
    HUGGINGFACE_BIOMISTRAL_MODEL: str = os.getenv(
        "HUGGINGFACE_BIOMISTRAL_MODEL", "BioMistral/BioMistral-7B"
    )
    HUGGINGFACE_MEDGEMMA_MODEL: str = os.getenv(
        "HUGGINGFACE_MEDGEMMA_MODEL", "google/medgemma-4b-it"
    )
    HUGGINGFACE_API_TOKEN: str = os.getenv("HUGGINGFACE_API_TOKEN", "")
    AI_PRIMARY_MODEL: str = os.getenv("AI_PRIMARY_MODEL", "biomistral")   # biomistral | medgemma
    AI_MAX_NEW_TOKENS: int = int(os.getenv("AI_MAX_NEW_TOKENS", "512"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.3"))

    # Ollama (optional fallback)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "biomistral")

    # Embeddings (for RAG)
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "512"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "64"))

    # ChromaDB
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    CHROMA_COLLECTION_PREFIX: str = "patient_"

    # OpenFDA Drug Database
    OPENFDA_API_URL: str = "https://api.fda.gov/drug/label.json"
    OPENFDA_TIMEOUT_SECONDS: int = 10

    # PaddleOCR
    PADDLE_OCR_LANG: str = "en"
    PADDLE_USE_ANGLE_CLS: bool = True

    # Health Analytics
    WEARABLE_ANOMALY_SIGMA: float = 2.0       # Flag if > 2 standard deviations from baseline
    BLOOD_OXYGEN_ALERT_THRESHOLD: float = 95.0  # SpO2 below this triggers alert
    INSIGHT_GENERATION_INTERVAL_DAYS: int = 7  # Weekly insights

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()

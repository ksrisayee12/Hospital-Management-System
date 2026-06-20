"""
MODULE 2 — PART B: Core Configuration
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class PartBSettings(BaseSettings):
    # ── Supabase ──────────────────────────────
    supabase_url: str
    supabase_key: str
    supabase_storage_bucket: str = "patient-vault"

    # ── Database ──────────────────────────────
    database_url: str                               # PostgreSQL DSN

    # ── Encryption ────────────────────────────
    aes_encryption_key: str                         # 32-byte hex key for AES-256
    aes_encryption_iv_salt: str

    # ── ChromaDB ──────────────────────────────
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection_prefix: str = "pspin_patient_"

    # ── Embedding Model ───────────────────────
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 32
    embedding_max_tokens: int = 512

    # ── AI Models ─────────────────────────────
    biomistral_model_path: str = "/models/BioMistral-7B"
    medgemma_model_path: str = "/models/medgemma"
    default_ai_model: str = "biomistral"            # biomistral | medgemma
    ai_max_tokens: int = 1024
    ai_temperature: float = 0.2

    # ── RAG ───────────────────────────────────
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.65
    rag_chunk_size: int = 400                       # tokens per chunk
    rag_chunk_overlap: int = 50

    # ── OCR ───────────────────────────────────
    paddleocr_lang: str = "en"
    ocr_confidence_threshold: float = 0.7
    ocr_max_file_size_mb: int = 10

    # ── Analytics ─────────────────────────────
    analytics_default_period_days: int = 30
    anomaly_z_score_threshold: float = 2.5

    # ── App ───────────────────────────────────
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    part_b_api_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> PartBSettings:
    return PartBSettings()

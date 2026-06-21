import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Vortexa Module 4 - Governance"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_DEV_SECRET")
    JWT_ALGORITHM: str = "HS256"
    
    FRAUD_VIEW_COUNT_THRESHOLD: int = 50
    FRAUD_DOWNLOAD_COUNT_THRESHOLD: int = 10
    FRAUD_OVERRIDE_WEEKLY_THRESHOLD: int = 5
    FRAUD_VIEW_WINDOW_MINUTES: int = 60
    FRAUD_DOWNLOAD_WINDOW_MINUTES: int = 60
    TRUST_SCORE_DEFAULT: int = 100
    TRUST_SCORE_COMPLAINT_PENALTY: int = 5
    TRUST_SCORE_ALERT_PENALTY: int = 5
    TRUST_SCORE_OVERRIDE_MISUSE_PENALTY: int = 10
    TRUST_SCORE_MIN: int = 0
    ENABLE_SEMANTIC_COMPLAINT_CLASSIFIER: bool = False

    class Config:
        env_file = ".env"

settings = Settings()

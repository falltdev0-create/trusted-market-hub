"""
Core Configuration — إعدادات النظام الأساسية
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "TrustedMarket"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "CHANGE_THIS_TO_A_STRONG_SECRET_KEY_IN_PRODUCTION"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/trusted_market"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    JWT_SECRET_KEY: str = "JWT_SECRET_CHANGE_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 30

    # Storage (MinIO / S3)
    STORAGE_ENDPOINT: str = "localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET_IMAGES: str = "trusted-images"
    STORAGE_BUCKET_DOCS: str = "trusted-documents"
    STORAGE_SECURE: bool = False

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://trustedmarket.app",
    ]

    # AI Models paths
    CONDITION_MODEL_PATH: str = "ai_models/condition_model/model.pt"
    DOCUMENT_MODEL_PATH: str = "ai_models/document_model/model.pt"
    PRICING_MODEL_PATH: str = "ai_models/pricing_model/model.pkl"

    # Price limits per condition and category (SAR / SDG — adjust as needed)
    PRICE_LIMITS: dict = {
        "house": {
            "sale": {"excellent": 5_000_000, "good": 3_000_000, "poor": 1_500_000},
            "rent": {"excellent": 10_000,    "good": 7_000,     "poor": 4_000},
        },
        "car": {
            "sale": {"excellent": 500_000, "good": 300_000, "poor": 150_000},
            "rent": {"excellent": 3_000,   "good": 2_000,   "poor": 1_000},
        },
    }

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

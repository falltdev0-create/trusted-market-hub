"""
app/core/config.py — إعدادات النظام الأساسية
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME:    str  = "maskan"
    APP_VERSION: str  = "2.0.0"
    DEBUG:       bool = False

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL:    str = "postgresql+asyncpg://postgres:password@localhost:5432/moamalati"
    DB_POOL_SIZE:    int = 20
    DB_MAX_OVERFLOW: int = 40

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY:            str = "CHANGE_IN_PRODUCTION"
    JWT_ALGORITHM:             str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS:   int = 30

    # ── Storage ───────────────────────────────────────────────────────────────
    # local = حفظ الملفات على قرص السيرفر (الافتراضي، يعمل دائماً)
    STORAGE_BACKEND:       str  = "local"
    STORAGE_LOCAL_DIR:     str  = "uploads"
    PUBLIC_BASE_URL:       str  = "http://localhost:8000"
    STORAGE_ENDPOINT:      str  = "localhost:9000"
    STORAGE_ACCESS_KEY:    str  = "minioadmin"
    STORAGE_SECRET_KEY:    str  = "minioadmin"
    STORAGE_BUCKET_IMAGES: str  = "moamalati-images"
    STORAGE_BUCKET_DOCS:   str  = "moamalati-docs"
    STORAGE_SECURE:        bool = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "https://moamalati.app",
    ]

    # ── AI Model Paths ────────────────────────────────────────────────────────
    CONDITION_MODEL_PATH: str = "ai_models/condition_model/weights/model.pt"
    DOCUMENT_MODEL_PATH:  str = "ai_models/document_model/weights/model.pt"
    PRICING_MODEL_PATH:   str = "ai_models/pricing_model/weights/model.pkl"

    # ── Price Caps (جنيه سوداني) ──────────────────────────────────────────────
    PRICE_CAPS: dict = {
        "house": {
            "sale": {"excellent": 8_000_000, "good": 5_000_000, "poor": 2_500_000},
            "rent": {"excellent": 80_000,    "good": 50_000,    "poor": 25_000},
        },
        "car": {
            "sale": {"excellent": 3_000_000, "good": 1_800_000, "poor": 900_000},
            "rent": {"excellent": 15_000,    "good": 10_000,    "poor": 5_000},
        },
    }

    '''class Config:
        env_file = ".env"
        case_sensitive = True'''


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

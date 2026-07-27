"""
app/core/config.py — إعدادات النظام الأساسية
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache
from pydantic import model_validator

HF_CONDITION_MODEL = "microsoft/resnet-50"
HF_DOCUMENT_MODEL = "microsoft/trocr-large-handwritten"
HF_PRICING_MODEL = "google/flan-t5-base"
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME:    str  = "maskan"
    APP_VERSION: str  = "2.0.0"
    DEBUG:       str | bool = False

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str | None = None
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "maskandaba"

    DB_POOL_SIZE:    int = 20
    DB_MAX_OVERFLOW: int = 40

    @model_validator(mode="after")
    def assemble_database_url(self):
        # Coerce DEBUG if it's accidentally provided as a string (e.g. 'release')
        if isinstance(self.DEBUG, str):
            self.DEBUG = self.DEBUG.lower() in ("1", "true", "yes", "y", "on")

        if self.DATABASE_URL:
            return self

        password_segment = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
        self.DATABASE_URL = (
            f"mysql+aiomysql://{self.DB_USER}{password_segment}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
        return self

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://127.0.0.1:6379"

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY:            str = "CHANGE_IN_PRODUCTION"
    JWT_ALGORITHM:             str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS:   int = 30

    # ── Storage (MinIO / S3) ──────────────────────────────────────────────────
    STORAGE_ENDPOINT:      str  = "localhost:9000"
    STORAGE_ACCESS_KEY:    str  = "minioadmin"
    STORAGE_SECRET_KEY:    str  = "minioadmin"
    STORAGE_BUCKET_IMAGES: str  = "moamalati-images"
    STORAGE_BUCKET_DOCS:   str  = "moamalati-docs"
    STORAGE_SECURE:        bool = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS_STR: str = "http://localhost:5173,http://localhost:3000"
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_STR.split(",")]

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

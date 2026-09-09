"""
معاملاتي — Backend Entry Point
FastAPI + SQLAlchemy Async + WebSocket Chat + AI Pipeline
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.core.config import settings
from app.core.database import create_tables
from app.api.routes import (
    auth, users, listings, verification, chat, search,
    admin, upload, kyc, notifications, rag,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} — started")
    yield
    print(f"🛑 {settings.APP_NAME} — shutting down")


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="معاملاتي backend API — FastAPI, Async SQLAlchemy, WebSocket Chat, AI Pipeline",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static uploads (كل الصور والوثائق المرفوعة) ───────────────────────────────
os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.STORAGE_LOCAL_DIR), name="uploads")

# ── Routers ───────────────────────────────────────────────────────────────────
V1 = "/api/v1"
app.include_router(auth.router,          prefix=f"{V1}/auth",          tags=["Auth"])
app.include_router(users.router,         prefix=f"{V1}/users",         tags=["Users"])
app.include_router(listings.router,      prefix=f"{V1}/listings",      tags=["Listings"])
app.include_router(verification.router,  prefix=f"{V1}/verification",  tags=["Verification"])
app.include_router(chat.router,          prefix=f"{V1}/chat",          tags=["Chat"])
app.include_router(search.router,        prefix=f"{V1}/search",        tags=["Search"])
app.include_router(admin.router,         prefix=f"{V1}/admin",         tags=["Admin"])
app.include_router(upload.router,        prefix=f"{V1}/upload",        tags=["Upload"])
app.include_router(notifications.router, prefix=f"{V1}/notifications", tags=["Notifications"])
app.include_router(rag.router,           prefix=f"{V1}/rag",           tags=["RAG"])
# kyc router already declares prefix="/kyc"
app.include_router(kyc.router,           prefix=V1)


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/api/v1/health")
async def health_v1():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

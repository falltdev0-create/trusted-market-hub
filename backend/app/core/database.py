"""
app/core/database.py — Database configuration and session management
Async SQLAlchemy + mySQL (aiomysql) setup for the Maskan application.
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine_kwargs = {
    "echo": settings.DEBUG,
    "pool_pre_ping": not settings.DATABASE_URL.startswith("mysql"),
}

if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
    })
else:
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
    })

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    from app.models import models  # noqa — registers all models
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        import logging
        logging.warning("Could not create database tables on startup: %s", exc)
        # Do not raise here; allow the application to continue starting so
        # the developer can inspect and fix DB credentials without failing
        # the whole service.
        return

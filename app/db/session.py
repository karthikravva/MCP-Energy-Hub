"""
Database session management for async SQLAlchemy
Supports PostgreSQL (production) and SQLite (development/HuggingFace)
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from app.config import get_settings
from app.models.database import Base

settings = get_settings()

# Determine database URL and pool settings
database_url = settings.database_url

# Check if using SQLite (for HuggingFace Spaces or local dev without PostgreSQL)
is_sqlite = database_url.startswith("sqlite")

# Create async engine with appropriate settings
if is_sqlite:
    # SQLite requires StaticPool for async and check_same_thread=False
    engine = create_async_engine(
        database_url,
        echo=settings.debug,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False} if "sqlite" in database_url else {},
    )
else:
    # PostgreSQL with NullPool for async
    engine = create_async_engine(
        database_url,
        echo=settings.debug,
        poolclass=NullPool,
    )

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    Drop all database tables (use with caution!)
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

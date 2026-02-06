"""
Database Configuration

SQLAlchemy database setup with connection pooling and session management.
"""

import logging
from typing import Optional

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from cloud_backend.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

engine = None
async_engine = None
SessionLocal = None
AsyncSessionLocal = None


def get_database_url() -> str:
    """Get database URL, converting to async format if needed."""
    db_url = settings.DATABASE_URL
    
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return db_url


def init_db():
    """Initialize database connection and create tables."""
    global engine, async_engine, SessionLocal, AsyncSessionLocal
    
    db_url = get_database_url()
    
    async_engine = create_async_engine(
        db_url,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DEBUG,
        future=True
    )
    
    AsyncSessionLocal = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    logger.info("Database initialized")
    
    return async_engine


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI to get database session.
    
    Yields a database session and ensures it's closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

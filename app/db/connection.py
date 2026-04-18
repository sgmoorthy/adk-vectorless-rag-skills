import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://admin:pass@localhost:5432/rag"
)

# Async engine for Vectorless RAG
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, pool_size=20)

SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db_session():
    """Dependency injection wrapper for retrieving an active Postgres session."""
    async with SessionLocal() as session:
        yield session

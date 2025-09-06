from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./chyrp.db"

# Create async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=True,
    connect_args={"check_same_thread": False}
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
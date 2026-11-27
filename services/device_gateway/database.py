import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://iot_admin:iot_secret_pass@localhost:5432/iot_qa_db",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Async SQLAlchemy engine and session factory for PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# Async Redis client helper
def get_redis_client() -> Redis:
    return Redis.from_url(REDIS_URL, decode_responses=True)

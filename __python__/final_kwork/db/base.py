"""
База SQLAlchemy 2.0 с async engine.
"""
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

# Async engine
engine = create_async_engine(settings.database_url, echo=False)

# Session factory
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


async def init_db() -> None:
    """Создание таблиц при запуске."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

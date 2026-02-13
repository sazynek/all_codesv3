# from typing import AsyncGenerator, Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


# Создаем базовый класс для моделей
class Base(AsyncAttrs, DeclarativeBase):
    pass


# Инициализация базы данных
class Database:
    def __init__(self, db_url: str = "sqlite+aiosqlite:///./test.db"):
        self.engine = create_async_engine(
            db_url, echo=True, future=True  # Включаем логирование SQL-запросов
        )

        self.engine = create_async_engine(db_url, echo=True)
        self.session = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_all_tables(self):
        """Создание всех таблиц"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("Все таблицы успешно созданы")

    async def drop_all_tables(self):
        """Удаление всех таблиц"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        print("Все таблицы успешно удалены")

    async def recreate_tables(self):
        """Пересоздание всех таблиц (удаление и создание заново)"""
        await self.drop_all_tables()
        await self.create_all_tables()


# Создаем глобальный экземпляр базы данных
db = Database()

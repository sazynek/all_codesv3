from .db_init import Base  # type: ignore
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import select, and_, func, select, delete, update
from typing import Any, Sequence
from sqlalchemy import func  # Добавьте этот импорт
from sqlalchemy.ext.asyncio import AsyncSession

# from typing import Optional


class PromptData(Base):
    __tablename__ = "taxi"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)

    text: Mapped[str] = mapped_column(index=True)


class Anecdote(Base):
    __tablename__ = "anecdotes"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)

    text: Mapped[str]
    time_to_start: Mapped[str]  # mb change data


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)
    tg_id: Mapped[int]  # change to BigInt

    text: Mapped[str]
    time_to_delete: Mapped[str]  # mb change data


class AdministerData(Base):
    __tablename__ = "administers"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)

    tabu: Mapped[list[str]]


class ParserUrl(Base):
    __tablename__ = "administers"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)

    url: Mapped[str]
    content: Mapped[str | None]


class Chats(Base):
    __tablename__ = "chats"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)

    chat: Mapped[str]


class Advertisement(Base):
    __tablename__ = "advertisements"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)

    text: Mapped[str]


# async def find_similar_taxis_db(
#     session: AsyncSession,
#     lvl: Optional[str] = None,
#     city: Optional[str] = None,
#     car: Optional[str] = None,
#     year: Optional[int] = None,
# ) -> Sequence[Taxi]:
#     """
#     Улучшенный поиск такси через БД с нормализацией регистра и обрезанием окончаний

#     Args:
#         session: Асинхронная сессия БД
#         lvl: Уровень такси (LIKE поиск, обрезаются окончания)
#         city: Город (LIKE поиск, обрезаются окончания)
#         car: Машина (LIKE поиск, обрезаются окончания)
#         year: Год выпуска (указанный_год >= года_в_бд)

#     Returns:
#         List[Taxi]: Список найденных такси
#     """

#     def normalize_like_param(text: str) -> str:
#         """Нормализует параметр для LIKE поиска: нижний регистр + обрезание"""
#         if not text:
#             return text

#         # Приводим к нижнему регистру
#         text_lower = text.strip().lower()

#         # Обрезаем окончание для LIKE поиска
#         return shorten_for_like(text_lower)

#     def shorten_for_like(text: str) -> str:
#         """Обрезает окончание (до 2 символов) для более эффективного LIKE поиска"""
#         if not text or len(text) <= 6:
#             return text
#         # Обрезаем 1-2 символа с конца, если это буквы
#         if text[-1].isalpha() and text[-2].isalpha():
#             return text[:-2]
#         elif text[-1].isalpha():
#             return text[:-1]
#         return text

#     conditions: list[Any] = []
#     search_params: dict[str, Any] = {}

#     # 1. Фильтр по году: year >= Taxi.year
#     if year is not None:
#         conditions.append(year >= Taxi.year)
#         search_params["year"] = year
#         print(f"✅ Фильтр по году: {year} >= taxi.year")

#     # 2. Обработка и поиск по остальным полям (полное приведение к нижнему регистру)
#     if lvl:
#         lvl_normalized = normalize_like_param(lvl)
#         # Приводим оба значения к нижнему регистру: func.lower(Taxi.lvl)
#         conditions.append(func.lower(Taxi.lvl).like(f"%{lvl_normalized}%"))
#         search_params["lvl"] = lvl
#         search_params["lvl_normalized"] = lvl_normalized
#         print(f"🔍 Поиск по lvl: '{lvl}' → lower(lvl) LIKE '%{lvl_normalized}%'")

#     if city:
#         city_normalized = normalize_like_param(city)
#         # Приводим поле city к нижнему регистру
#         conditions.append(func.lower(Taxi.city).like(f"%{city_normalized}%"))
#         search_params["city"] = city
#         search_params["city_normalized"] = city_normalized
#         print(f"🏙️ Поиск по city: '{city}' → lower(city) LIKE '%{city_normalized}%'")

#     if car:
#         car_normalized = normalize_like_param(car)
#         # Приводим поле car к нижнему регистру
#         conditions.append(func.lower(Taxi.car).like(f"%{car_normalized}%"))
#         search_params["car"] = car
#         search_params["car_normalized"] = car_normalized
#         print(f"🚗 Поиск по car: '{car}' → lower(car) LIKE '%{car_normalized}%'")

#     # 3. Логирование параметров поиска
#     if search_params:
#         print(f"📊 Параметры поиска: {search_params}")

#     # 4. Строим запрос
#     if conditions:
#         stmt = select(Taxi).where(and_(*conditions))
#     else:
#         stmt = select(Taxi)

#     # 5. Выполняем запрос
#     result = await session.execute(stmt)
#     taxis = result.scalars().all()

#     print(f"✅ Найдено такси: {len(taxis)}")
#     return taxis

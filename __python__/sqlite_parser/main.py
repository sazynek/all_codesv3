import asyncio
from db.db_init import db
from db.models import create_taxi, find_similar_taxis_db
from parse_user_input import to_ollama
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any


async def create_test_taxis(session: AsyncSession):
    test_taxis: list[Any] = [
        # Базовые популярные тарифы
        {"year": 2022, "car": "Kia Rio", "city": "Москва", "lvl": "Комфорт"},
        {
            "year": 2023,
            "car": "Hyundai Solaris",
            "city": "Санкт-Петербург",
            "lvl": "Эконом",
        },
        {"year": 2021, "car": "Toyota Camry", "city": "Казань", "lvl": "Комфорт+"},
        # Бизнес-класс и премиум
        {
            "year": 2023,
            "car": "Mercedes E-Class",
            "city": "Москва",
            "lvl": "Ultima: Business",
        },
        {
            "year": 2022,
            "car": "BMW 5 Series",
            "city": "Санкт-Петербург",
            "lvl": "Ultima: Premier",
        },
        {
            "year": 2024,
            "car": "Audi A6",
            "city": "Екатеринбург",
            "lvl": "Ultima: Elite",
        },
        # Минивэны и грузовые
        {
            "year": 2020,
            "car": "Volkswagen Multivan",
            "city": "Новосибирск",
            "lvl": "Минивэн",
        },
        {"year": 2019, "car": "Toyota Hiace", "city": "Краснодар", "lvl": "Минивэн"},
        {
            "year": 2021,
            "car": "Ford Transit",
            "city": "Ростов-на-Дону",
            "lvl": "Помощь взрослым",
        },
        # Детские тарифы
        {"year": 2023, "car": "Skoda Octavia", "city": "Москва", "lvl": "Детский"},
        {
            "year": 2022,
            "car": "Lada Vesta",
            "city": "Нижний Новгород",
            "lvl": "Помощь детям",
        },
        # Межгород
        {"year": 2021, "car": "Kia Sorento", "city": "Москва", "lvl": "Межгород"},
        {
            "year": 2022,
            "car": "Toyota RAV4",
            "city": "Санкт-Петербург",
            "lvl": "Межгород",
        },
        # С водителем
        {"year": 2023, "car": "Lexus ES", "city": "Сочи", "lvl": "Ultima: Водитель"},
        # Старые машины для проверки фильтрации по году
        {"year": 2015, "car": "Ford Focus", "city": "Воронеж", "lvl": "Эконом"},
        {"year": 2010, "car": "Chevrolet Lacetti", "city": "Самара", "lvl": "Эконом"},
        # Разные марки для проверки поиска
        {"year": 2022, "car": "Chery Tiggo", "city": "Уфа", "lvl": "Комфорт"},
        {"year": 2023, "car": "Geely Coolray", "city": "Пермь", "lvl": "Комфорт+"},
        {"year": 2021, "car": "Haval Jolion", "city": "Волгоград", "lvl": "Комфорт"},
        # Одинаковые машины в разных городах
        {"year": 2023, "car": "Kia Rio", "city": "Екатеринбург", "lvl": "Комфорт"},
        {"year": 2023, "car": "Kia Rio", "city": "Новосибирск", "lvl": "Комфорт"},
        # Одинаковые тарифы с разными марками
        {"year": 2022, "car": "Hyundai Creta", "city": "Москва", "lvl": "Комфорт+"},
        {"year": 2022, "car": "Volkswagen Tiguan", "city": "Москва", "lvl": "Комфорт+"},
        # Граничные случаи
        {
            "year": 2024,
            "car": "Tesla Model 3",
            "city": "Москва",
            "lvl": "Ultima: Business",
        },
        {"year": 2020, "car": "Škoda Rapid", "city": "Калининград", "lvl": "Комфорт"},
    ]

    created_count = 0
    for taxi_data in test_taxis:
        try:
            await create_taxi(
                session,
                year=taxi_data["year"],
                car=taxi_data["car"],
                city=taxi_data["city"],
                lvl=taxi_data["lvl"],
            )
            created_count += 1
            print(
                f"✅ Создано такси: {taxi_data['car']} ({taxi_data['year']}) в {taxi_data['city']} - {taxi_data['lvl']}"
            )
        except Exception as e:
            print(f"❌ Ошибка при создании такси {taxi_data['car']}: {e}")

    return created_count


async def main():
    await db.recreate_tables()

    try:
        async with db.session() as session:
            pass

    except Exception as e:
        print(f"\n⚠️ Ошибка при работе с БД: {e}")

    finally:
        await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

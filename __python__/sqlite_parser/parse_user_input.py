import ollama
import json
from typing import Any


def to_ollama(
    text: str,
    model_name: str = "gemma3:4b",
) -> dict[str, Any]:
    system_prompt = f""
    user_prompt = f"Текст: {text}"

    try:
        # Отправляем запрос в модель
        response = ollama.chat(  # type: ignore
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={
                "temperature": 0.4,  # Меньше креативности, больше следования инструкциям
                # "keep_alive": '30m'
            },
        )
        # Пытаемся получить и распарсить JSON из ответа модели
        response_content = response["message"]["content"]
        print(f"response {response_content}")

        return {}

    except json.JSONDecodeError as e:
        print(f"Не удалось распарсить JSON из ответа модели: {e}")
        print(f"Сырой ответ модели: {response_content}")  # type: ignore
        print(f"error: Ошибка парсинга raw_response: {response_content}")  # type: ignore
        return {"city": None, "lvl": None, "year": None, "car": None}  # type: ignore
    except Exception as e:
        print(f"Проанализировал тест: {e}")
        print(f"Ошибка: {str(e)}")
        return {"city": None, "lvl": None, "year": None, "car": None}

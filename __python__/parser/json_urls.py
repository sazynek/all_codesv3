import json
import os
from config import *


def save_json(data, filename: str):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  Ошибка при сохранении в {filename}: {e}")


def load_json(filename: str, default=None):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"  Ошибка при загрузке из {filename}: {e}")
    return default if default is not None else {}

from __future__ import annotations
import functools
from enum import Enum, auto
from typing import (
    Callable,
    overload,
    Sequence,
    Optional,
    Any,
    Union,
    Literal,
    cast,
)
import math
import statistics
import json
import hashlib
import secrets
from datetime import datetime, timedelta
import re
import base64

# Типы для данных
StringOrNumber = Union[str, int, float]


class TextOperationType(Enum):
    AddToStart = auto()
    AddToEnd = auto()
    AddTo = auto()
    Format = auto()
    Split = auto()
    Calc = auto()
    Power = auto()
    MathOp = auto()


class TextOperationConfig:
    pass


class AddToStartConfig(TextOperationConfig):
    def __init__(self, text: str):
        self.text = text


class AddToEndConfig(TextOperationConfig):
    def __init__(self, text: str):
        self.text = text


class AddToConfig(TextOperationConfig):
    def __init__(self, text: str, position: Literal["start", "end"]):
        self.text = text
        self.position = position


class FormatConfig(TextOperationConfig):
    def __init__(self, template: str, **kwargs: Any):
        self.template = template
        self.kwargs = kwargs


class SplitConfig(TextOperationConfig):
    def __init__(self, separator: Optional[str] = None):
        self.separator = separator


class CalcConfig(TextOperationConfig):
    def __init__(self, operation: Callable[[Any], Any], **kwargs: Any):
        self.operation = operation
        self.kwargs = kwargs


class PowerConfig(TextOperationConfig):
    def __init__(self, exponent: float):
        self.exponent = exponent


class MathOpConfig(TextOperationConfig):
    def __init__(self, operation: str, value: float):
        self.operation = operation
        self.value = value


class TextProcessor:
    """Процессор для работы со строками и числами"""

    def __init__(self, data: StringOrNumber):
        self.data = data

    def process(
        self,
        operation: TextOperationType,
        config: TextOperationConfig,
    ) -> StringOrNumber | Sequence[str]:
        return self._try_operation(operation, config)

    def _try_operation(
        self, operation: TextOperationType, config: TextOperationConfig
    ) -> StringOrNumber | Sequence[str]:
        match operation:
            case TextOperationType.AddToStart:
                return self._add_to_start(config)  # type: ignore
            case TextOperationType.AddToEnd:
                return self._add_to_end(config)  # type: ignore
            case TextOperationType.AddTo:
                return self._add_to(config)  # type: ignore
            case TextOperationType.Format:
                return self._format(config)  # type: ignore
            case TextOperationType.Split:
                return self._split(config)  # type: ignore
            case TextOperationType.Calc:
                return self._calc(config)  # type: ignore
            case TextOperationType.Power:
                return self._power(config)  # type: ignore
            case TextOperationType.MathOp:
                return self._math_operation(config)  # type: ignore
            case _:
                raise ValueError(f"Неизвестная операция: {operation}")

    def _add_to_start(self, config: AddToStartConfig) -> str:
        """Добавляет текст в начало"""
        return config.text + str(self.data)

    def _add_to_end(self, config: AddToEndConfig) -> str:
        """Добавляет текст в конец"""
        return str(self.data) + config.text

    def _add_to(self, config: AddToConfig) -> str:
        """Добавляет текст в указанную позицию"""
        if config.position == "start":
            return config.text + str(self.data)
        else:
            return str(self.data) + config.text

    def _format(self, config: FormatConfig) -> str:
        """Форматирует результат по шаблону"""
        result_str = str(self.data)
        # Заменяем {origin} на исходный результат
        formatted = config.template.replace("{origin}", result_str)

        # Заменяем другие плейсхолдеры из kwargs
        for key, value in config.kwargs.items():
            placeholder = "{" + key + "}"
            formatted = formatted.replace(placeholder, str(value))

        return formatted

    def _split(self, config: SplitConfig) -> Sequence[str]:
        """Разделяет строку на слова (только для строк)"""
        if not isinstance(self.data, str):
            return [str(self.data)]

        if config.separator is not None:
            return self.data.split(config.separator)
        else:
            # Разделение по пробелам по умолчанию
            return self.data.split()

    def _calc(self, config: CalcConfig) -> StringOrNumber:
        """Применяет функцию к числу (только для чисел)"""
        if not isinstance(self.data, (int, float)):
            return self.data

        try:
            return config.operation(self.data, **config.kwargs)
        except Exception:
            return self.data

    def _power(self, config: PowerConfig) -> StringOrNumber:
        """Возводит число в степень (только для чисел)"""
        if not isinstance(self.data, (int, float)):
            return self.data

        try:
            return self.data**config.exponent
        except Exception:
            return self.data

    def _math_operation(self, config: MathOpConfig) -> StringOrNumber:
        """Выполняет математическую операцию (только для чисел)"""
        if not isinstance(self.data, (int, float)):
            return self.data

        try:
            if config.operation == "add":
                return self.data + config.value
            elif config.operation == "subtract":
                return self.data - config.value
            elif config.operation == "multiply":
                return self.data * config.value
            elif config.operation == "divide":
                if config.value == 0:
                    return self.data
                return self.data / config.value
            elif config.operation == "modulo":
                if config.value == 0:
                    return self.data
                return self.data % config.value
            else:
                return self.data
        except Exception:
            return self.data


def _should_process_text(value: Any) -> bool:
    """Проверяет, можно ли обработать значение"""
    return isinstance(value, (str, int, float))


# === ДЕКОРАТОР ADD_TO_START ===
@overload
def add_to_start(func: Callable[..., str | int | float]) -> Callable[..., str]: ...


@overload
def add_to_start(
    *, text: str
) -> Callable[[Callable[..., str | int | float]], Callable[..., str]]: ...


def add_to_start(
    func: Callable[..., str | int | float] | None = None,
    *,
    text: str | None = None,
) -> (
    Callable[..., str]
    | Callable[[Callable[..., str | int | float]], Callable[..., str]]
):

    if text is None:
        raise ValueError("Text parameter is required")

    def decorator(f: Callable[..., str | int | float]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            if _should_process_text(result):
                processor = TextProcessor(result)
                config = AddToStartConfig(text=text)
                processed = processor.process(
                    operation=TextOperationType.AddToStart,
                    config=config,
                )
                return cast(str, processed)
            return str(result)

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР ADD_TO_END ===
@overload
def add_to_end(func: Callable[..., str | int | float]) -> Callable[..., str]: ...


@overload
def add_to_end(
    *, text: str
) -> Callable[[Callable[..., str | int | float]], Callable[..., str]]: ...


def add_to_end(
    func: Callable[..., str | int | float] | None = None,
    *,
    text: str | None = None,
) -> (
    Callable[..., str]
    | Callable[[Callable[..., str | int | float]], Callable[..., str]]
):

    if text is None:
        raise ValueError("Text parameter is required")

    def decorator(f: Callable[..., str | int | float]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            if _should_process_text(result):
                processor = TextProcessor(result)
                config = AddToEndConfig(text=text)
                processed = processor.process(
                    operation=TextOperationType.AddToEnd,
                    config=config,
                )
                return cast(str, processed)
            return str(result)

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР ADD_TO ===
@overload
def add_to(func: Callable[..., str | int | float]) -> Callable[..., str]: ...


@overload
def add_to(
    *, text: str, position: Literal["start", "end"]
) -> Callable[[Callable[..., str | int | float]], Callable[..., str]]: ...


def add_to(
    func: Callable[..., str | int | float] | None = None,
    *,
    text: str | None = None,
    position: Literal["start", "end"] = "start",
) -> (
    Callable[..., str]
    | Callable[[Callable[..., str | int | float]], Callable[..., str]]
):

    if text is None:
        raise ValueError("Text parameter is required")

    def decorator(f: Callable[..., str | int | float]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            if _should_process_text(result):
                processor = TextProcessor(result)
                config = AddToConfig(text=text, position=position)
                processed = processor.process(
                    operation=TextOperationType.AddTo,
                    config=config,
                )
                return cast(str, processed)
            return str(result)

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР FORMATTER ===
def formatter(
    template: str,
    **kwargs: Any,
) -> Callable[[Callable[..., str | int | float]], Callable[..., str]]:
    def decorator(f: Callable[..., str | int | float]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs_inner: Any) -> str:
            result = f(*args, **kwargs_inner)
            if _should_process_text(result):
                processor = TextProcessor(result)
                config = FormatConfig(template=template, **kwargs)
                processed = processor.process(
                    operation=TextOperationType.Format,
                    config=config,
                )
                return cast(str, processed)
            return str(result)

        return wrapper

    return decorator


# === ДЕКОРАТОР SPLIT_STR ===
@overload
def split_str[**P, R: StringOrNumber](
    func: Callable[P, R],
) -> Callable[P, Sequence[str]]: ...


@overload
def split_str[**P, R: StringOrNumber](
    *,
    separator: Optional[str] = None,
) -> Callable[[Callable[P, R]], Callable[P, Sequence[str] | R]]: ...


def split_str[**P, R: StringOrNumber](
    func: Callable[P, R] | None = None,
    *,
    separator: Optional[str] = None,
) -> (
    Callable[P, Sequence[str]]
    | Callable[[Callable[P, R]], Callable[P, Sequence[str] | R]]
):
    def decorator(f: Callable[P, R]) -> Callable[P, Sequence[str]]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Sequence[str]:
            result = f(*args, **kwargs)
            if _should_process_text(result):
                processor = TextProcessor(result)
                config = SplitConfig(separator=separator)
                processed = processor.process(
                    operation=TextOperationType.Split,
                    config=config,
                )
                return cast(Sequence[str], processed)
            return [str(result)]

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР POWER ===
@overload
def power(
    func: Callable[..., str | int | float],
) -> Callable[..., str | int | float]: ...


@overload
def power(
    *, exponent: float
) -> Callable[[Callable[..., str | int | float]], Callable[..., str | int | float]]: ...


def power(
    func: Callable[..., str | int | float] | None = None,
    *,
    exponent: float | None = None,
) -> (
    Callable[..., str | int | float]
    | Callable[[Callable[..., str | int | float]], Callable[..., str | int | float]]
):

    if exponent is None:
        raise ValueError("Exponent parameter is required")

    def decorator(
        f: Callable[..., str | int | float],
    ) -> Callable[..., str | int | float]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str | int | float:
            result = f(*args, **kwargs)
            if _should_process_text(result):
                processor = TextProcessor(result)
                config = PowerConfig(exponent=exponent)
                processed = processor.process(
                    operation=TextOperationType.Power,
                    config=config,
                )
                return cast(str | int | float, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР CALC ===
def calc(
    operation: Callable[..., int | float],
    **kwargs: Any,
) -> Callable[[Callable[..., int | float]], Callable[..., int | float]]:
    def decorator(f: Callable[..., int | float]) -> Callable[..., int | float]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs_inner: Any) -> int | float:
            result = f(*args, **kwargs_inner)
            if _should_process_text(result):
                processor = TextProcessor(result)
                config = CalcConfig(operation=operation, **kwargs)
                processed = processor.process(
                    operation=TextOperationType.Calc,
                    config=config,
                )
                if isinstance(processed, (int, float)):
                    return processed
            return result

        return wrapper

    return decorator


# === ДЕКОРАТОР MATH OPERATIONS ===
def add[**P, R: StringOrNumber](
    value: float,
) -> Callable[[Callable[P, R]], Callable[P, StringOrNumber | R]]:
    """Добавляет значение к числу"""

    def decorator(f: Callable[P, R]) -> Callable[P, StringOrNumber]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> StringOrNumber:
            result = f(*args, **kwargs)
            if _should_process_text(result):
                processor = TextProcessor(result)
                config = MathOpConfig(operation="add", value=value)
                processed = processor.process(
                    operation=TextOperationType.MathOp,
                    config=config,
                )
                return cast(StringOrNumber, processed)
            return result

        return wrapper

    return decorator


def subtract[**P, R: StringOrNumber](
    value: float,
) -> Callable[[Callable[P, R]], Callable[P, StringOrNumber | R]]:
    """Вычитает значение из числа"""

    def decorator(f: Callable[P, R]) -> Callable[P, StringOrNumber]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> StringOrNumber:
            result = f(*args, **kwargs)
            if _should_process_text(result):
                processor = TextProcessor(result)
                config = MathOpConfig(operation="subtract", value=value)
                processed = processor.process(
                    operation=TextOperationType.MathOp,
                    config=config,
                )
                return cast(StringOrNumber, processed)
            return result

        return wrapper

    return decorator


def multiply[**P, R: StringOrNumber](
    value: float,
) -> Callable[[Callable[P, R]], Callable[P, StringOrNumber | R]]:
    """Умножает число на значение"""

    def decorator(f: Callable[P, R]) -> Callable[P, StringOrNumber]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> StringOrNumber:
            result = f(*args, **kwargs)
            if _should_process_text(result):
                processor = TextProcessor(result)
                config = MathOpConfig(operation="multiply", value=value)
                processed = processor.process(
                    operation=TextOperationType.MathOp,
                    config=config,
                )
                return cast(StringOrNumber, processed)
            return result

        return wrapper

    return decorator


def divide[**P, R: StringOrNumber](
    value: float,
) -> Callable[[Callable[P, R]], Callable[P, StringOrNumber | R]]:
    """Делит число на значение"""

    def decorator(f: Callable[P, R]) -> Callable[P, StringOrNumber]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> StringOrNumber:
            result = f(*args, **kwargs)
            if _should_process_text(result):
                processor = TextProcessor(result)
                config = MathOpConfig(operation="divide", value=value)
                processed = processor.process(
                    operation=TextOperationType.MathOp,
                    config=config,
                )
                return cast(StringOrNumber, processed)
            return result

        return wrapper

    return decorator


# === СЛОЖНЫЕ ЧИСЛОВЫЕ ДЕКОРАТОРЫ ===


def round_to(
    decimals: int = 0,
) -> Callable[[Callable[..., int | float]], Callable[..., int | float]]:
    """Округление до указанного количества знаков"""

    def decorator(f: Callable[..., int | float]) -> Callable[..., int | float]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> int | float:
            result = f(*args, **kwargs)
            return round(result, decimals)

        return wrapper

    return decorator


def clamp(
    min_val: float, max_val: float
) -> Callable[[Callable[..., int | float]], Callable[..., float]]:
    """Ограничение значения в диапазоне"""

    def decorator(f: Callable[..., int | float]) -> Callable[..., float]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> float:
            result = f(*args, **kwargs)
            return max(min_val, min(max_val, float(result)))

        return wrapper

    return decorator


def normalize(
    min_val: float = 0, max_val: float = 1
) -> Callable[[Callable[..., int | float]], Callable[..., float]]:
    """Нормализация значения в диапазон [0, 1] или указанный"""

    def decorator(f: Callable[..., int | float]) -> Callable[..., float]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> float:
            result = f(*args, **kwargs)
            # Для демонстрации используем фиксированный исходный диапазон
            original_min, original_max = 0, 100
            normalized = (result - original_min) / (original_max - original_min)
            return min_val + normalized * (max_val - min_val)

        return wrapper

    return decorator


def logarithmic(
    base: float = 10,
) -> Callable[[Callable[..., int | float]], Callable[..., float]]:
    """Логарифмическое преобразование"""

    def decorator(f: Callable[..., int | float]) -> Callable[..., float]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> float:
            result = f(*args, **kwargs)
            return math.log(result, base)

        return wrapper

    return decorator


def percentage(
    total: float = 100,
) -> Callable[[Callable[..., int | float]], Callable[..., float]]:
    """Преобразование в проценты"""

    def decorator(f: Callable[..., int | float]) -> Callable[..., float]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> float:
            result = f(*args, **kwargs)
            return (result / total) * 100

        return wrapper

    return decorator


def scientific_notation(
    precision: int = 2,
) -> Callable[[Callable[..., int | float]], Callable[..., str]]:
    """Преобразование в научную нотацию"""

    def decorator(f: Callable[..., int | float]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            return f"{result:.{precision}e}"

        return wrapper

    return decorator


# === СТАТИСТИЧЕСКИЕ ОПЕРАЦИИ ===


def moving_average(
    window: int = 3,
) -> Callable[[Callable[..., list[int | float]]], Callable[..., list[float]]]:
    """Скользящее среднее для списков чисел"""

    def decorator(f: Callable[..., list[int | float]]) -> Callable[..., list[float]]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> list[float]:
            result = f(*args, **kwargs)
            return [
                statistics.mean(result[max(0, i - window + 1) : i + 1])
                for i in range(len(result))
            ]

        return wrapper

    return decorator


def z_score() -> (
    Callable[[Callable[..., list[int | float]]], Callable[..., list[float]]]
):
    """Z-оценка для нормализации данных"""

    def decorator(f: Callable[..., list[int | float]]) -> Callable[..., list[float]]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> list[float]:
            result = f(*args, **kwargs)
            mean_val = statistics.mean(result)
            try:
                stdev_val = statistics.stdev(result)
                # Если стандартное отклонение равно 0, все элементы одинаковы
                # В этом случае z-оценки будут 0 для всех элементов
                if stdev_val == 0:
                    return [0.0 for _ in result]
                return [(x - mean_val) / stdev_val for x in result]
            except statistics.StatisticsError:
                # Обработка случаев, когда stdev не может быть вычислено
                return [0.0 for _ in result]

        return wrapper

    return decorator


# === СЛОЖНЫЕ СТРОКОВЫЕ ДЕКОРАТОРЫ ===


def regex_extract(
    pattern: str, group: int = 0
) -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Извлечение текста по регулярному выражению"""

    def decorator(f: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            match = re.search(pattern, result)
            return match.group(group) if match else ""

        return wrapper

    return decorator


def regex_replace(
    pattern: str, replacement: str
) -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Замена по регулярному выражению"""

    def decorator(f: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)

            return re.sub(pattern, replacement, result)

        return wrapper

    return decorator


def case_transform(
    case_type: str,
) -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Трансформация регистра"""

    def decorator(f: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            if case_type == "upper":
                return result.upper()
            elif case_type == "lower":
                return result.lower()
            elif case_type == "title":
                return result.title()
            elif case_type == "swapcase":
                return result.swapcase()
            elif case_type == "capitalize":
                return result.capitalize()
            else:
                return result

        return wrapper

    return decorator


def hash_string(
    algorithm: str = "md5",
) -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Хеширование строки"""

    def decorator(f: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            if algorithm == "md5":
                return hashlib.md5(result.encode()).hexdigest()
            elif algorithm == "sha1":
                return hashlib.sha1(result.encode()).hexdigest()
            elif algorithm == "sha256":
                return hashlib.sha256(result.encode()).hexdigest()
            return ""

        return wrapper

    return decorator


def encode_base64() -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Base64 кодирование"""

    def decorator(f: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            return base64.b64encode(result.encode()).decode()

        return wrapper

    return decorator


def decode_base64() -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Base64 декодирование"""

    def decorator(f: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            try:
                return base64.b64decode(result.encode()).decode()
            except Exception:
                return ""

        return wrapper

    return decorator


def slugify() -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Транслитерация в slug"""

    def decorator(f: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            # Простая реализация slugify
            slug = result.lower()
            slug = re.sub(r"[^a-z0-9]+", "-", slug)
            slug = slug.strip("-")
            return slug

        return wrapper

    return decorator


def truncate(
    max_length: int, suffix: str = "..."
) -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Обрезка строки с добавлением суффикса"""

    def decorator(f: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            return result[: max_length - len(suffix)] + suffix

        return wrapper

    return decorator


def trigonometric(
    operation: str,
) -> Callable[[Callable[..., float]], Callable[..., float]]:
    """Тригонометрические функции"""

    def decorator(f: Callable[..., float]) -> Callable[..., float]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> float:
            result = f(*args, **kwargs)
            rad = math.radians(result)  # предполагаем ввод в градусах
            if operation == "sin":
                return math.sin(rad)
            elif operation == "cos":
                return math.cos(rad)
            elif operation == "tan":
                return math.tan(rad)
            else:
                return rad

        return wrapper

    return decorator


def format_datetime(
    format_str: str = "%Y-%m-%d %H:%M:%S",
) -> Callable[[Callable[..., datetime]], Callable[..., str]]:
    """Форматирование datetime в строку"""

    def decorator(f: Callable[..., datetime]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            return result.strftime(format_str)

        return wrapper

    return decorator


def add_timedelta(
    **delta_kwargs: Any,
) -> Callable[[Callable[..., datetime]], Callable[..., datetime]]:
    """Добавление временного интервала к datetime"""

    def decorator(f: Callable[..., datetime]) -> Callable[..., datetime]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> datetime:
            result = f(*args, **kwargs)
            return result + timedelta(**delta_kwargs)

        return wrapper

    return decorator


def timestamp() -> Callable[[Callable[..., datetime]], Callable[..., float]]:
    """Преобразование datetime в timestamp"""

    def decorator(f: Callable[..., datetime]) -> Callable[..., float]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> float:
            result = f(*args, **kwargs)
            return result.timestamp()

        return wrapper

    return decorator


def currency_format(
    currency: str = "USD", decimals: int = 2
) -> Callable[[Callable[..., float]], Callable[..., str]]:
    """Форматирование валюты"""

    def decorator(f: Callable[..., float]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            return f"{currency} {result:,.{decimals}f}"

        return wrapper

    return decorator


def compound_interest(
    periods: int, rate: float
) -> Callable[[Callable[..., float]], Callable[..., float]]:
    """Расчет сложного процента"""

    def decorator(f: Callable[..., float]) -> Callable[..., float]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> float:
            principal = f(*args, **kwargs)
            return principal * (1 + rate) ** periods

        return wrapper

    return decorator


def tax_calculation(
    tax_rate: float,
) -> Callable[[Callable[..., float]], Callable[..., tuple[float, float]]]:
    """Расчет налога и чистой суммы"""

    def decorator(f: Callable[..., float]) -> Callable[..., tuple[float, float]]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> tuple[float, float]:
            amount = f(*args, **kwargs)
            tax = amount * tax_rate
            net_amount = amount - tax
            return net_amount, tax

        return wrapper

    return decorator


def distance_to(
    lat: float, lon: float
) -> Callable[[Callable[..., tuple[float, float]]], Callable[..., float]]:
    """Расчет расстояния между двумя точками (в км)"""

    def decorator(f: Callable[..., tuple[float, float]]) -> Callable[..., float]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> float:
            point_lat, point_lon = f(*args, **kwargs)

            # Формула гаверсинусов
            R = 6371  # Радиус Земли в км
            dlat = math.radians(lat - point_lat)
            dlon = math.radians(lon - point_lon)
            a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
                math.radians(point_lat)
            ) * math.cos(math.radians(lat)) * math.sin(dlon / 2) * math.sin(dlon / 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        return wrapper

    return decorator


def coordinate_format(
    format_type: str = "dms",
) -> Callable[[Callable[..., tuple[float, float]]], Callable[..., str]]:
    """Форматирование координат"""

    def decorator(f: Callable[..., tuple[float, float]]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            lat, lon = f(*args, **kwargs)

            if format_type == "dms":

                def to_dms(coord: float) -> str:
                    degrees = int(coord)
                    minutes = int((coord - degrees) * 60)
                    seconds = (coord - degrees - minutes / 60) * 3600
                    return f"{degrees}°{minutes}'{seconds:.2f}\""

                return f"{to_dms(lat)} N, {to_dms(lon)} E"
            else:
                return f"{lat:.6f}, {lon:.6f}"

        return wrapper

    return decorator


def one_hot_encode(
    categories: list[str],
) -> Callable[[Callable[..., str]], Callable[..., dict[str, int]]]:
    """One-hot encoding для категориальных данных"""

    def decorator(f: Callable[..., str]) -> Callable[..., dict[str, int]]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, int]:
            result = f(*args, **kwargs)
            return {category: 1 if category == result else 0 for category in categories}

        return wrapper

    return decorator


def min_max_scale(
    feature_range: tuple[float, float] = (0, 1)
) -> Callable[[Callable[..., list[float]]], Callable[..., list[float]]]:
    """Масштабирование признаков"""

    def decorator(f: Callable[..., list[float]]) -> Callable[..., list[float]]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> list[float]:
            data = f(*args, **kwargs)
            if not data:
                return []

            min_val = min(data)
            max_val = max(data)

            if max_val == min_val:
                return [feature_range[0]] * len(data)

            scaled = [
                feature_range[0]
                + (x - min_val)
                * (feature_range[1] - feature_range[0])
                / (max_val - min_val)
                for x in data
            ]
            return scaled

        return wrapper

    return decorator


def feature_engineering(
    operations: list[str],
) -> Callable[[Callable[..., list[float]]], Callable[..., dict[str, float]]]:
    """Инженерия признаков"""

    def decorator(f: Callable[..., list[float]]) -> Callable[..., dict[str, float]]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, float]:
            data = f(*args, **kwargs)
            features = {}

            if "mean" in operations:
                features["mean"] = statistics.mean(data) if data else 0
            if "std" in operations:
                features["std"] = statistics.stdev(data) if len(data) > 1 else 0
            if "min" in operations:
                features["min"] = min(data) if data else 0
            if "max" in operations:
                features["max"] = max(data) if data else 0
            if "range" in operations:
                features["range"] = features.get("max", 0) - features.get("min", 0)

            return features

        return wrapper

    return decorator


def json_serialize() -> Callable[[Callable[..., Any]], Callable[..., str]]:
    """Сериализация в JSON"""

    def decorator(f: Callable[..., Any]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            result = f(*args, **kwargs)
            return json.dumps(result, ensure_ascii=False, indent=2)

        return wrapper

    return decorator


def api_response(
    status: str = "success",
) -> Callable[[Callable[..., Any]], Callable[..., dict[str, Any]]]:
    """Форматирование API ответа"""

    def decorator(f: Callable[..., Any]) -> Callable[..., dict[str, Any]]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            try:
                data = f(*args, **kwargs)
                return {
                    "status": status,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }

        return wrapper

    return decorator


def validate_schema(
    schema: dict[str, type],
) -> Callable[[Callable[..., dict[str, Any]]], Callable[..., dict[str, Any]]]:
    """Валидация данных по схеме"""

    def decorator(f: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            data = f(*args, **kwargs)
            validated = {}
            errors = []

            for key, expected_type in schema.items():
                if key in data:
                    if isinstance(data[key], expected_type):
                        validated[key] = data[key]
                    else:
                        errors.append(
                            f"Field '{key}' should be {expected_type.__name__}"
                        )
                else:
                    errors.append(f"Missing required field: '{key}'")

            if errors:
                return {"valid": False, "errors": errors}
            return {"valid": True, "data": validated}

        return wrapper

    return decorator


def hash_sensitive(
    algorithm: str = "sha256", salt_length: int = 16
) -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Хеширование чувствительных данных с солью"""

    def decorator(f: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            data = f(*args, **kwargs)
            salt = secrets.token_hex(salt_length)
            if algorithm == "sha256":
                return hashlib.sha256((data + salt).encode()).hexdigest()
            elif algorithm == "sha512":
                return hashlib.sha512((data + salt).encode()).hexdigest()
            return data

        return wrapper

    return decorator


def mask_sensitive(
    mask_char: str = "*", visible_chars: int = 4
) -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Маскирование чувствительных данных"""

    def decorator(f: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> str:
            data = f(*args, **kwargs)
            if len(data) <= visible_chars:
                return mask_char * len(data)
            return data[:visible_chars] + mask_char * (len(data) - visible_chars)

        return wrapper

    return decorator

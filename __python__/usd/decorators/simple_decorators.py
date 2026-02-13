import functools  # type: ignore
import time
from typing import Any, Callable, overload, TypeVar, ParamSpec  # type: ignore
from collections import deque
from pathlib import Path  # type: ignore
import pickle  # type: ignore
import hashlib  # type: ignore

t = Callable[..., Any]


# ---------------------------------------------------- TIMER----------------------------------------------------
@overload
def timer[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def timer[**P, R](
    *,
    verbose: bool = True,
    shortname: bool = True,
    log_args: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def timer[**P, R](
    func: Callable[P, R] | None = None,
    *,
    verbose: bool = True,
    shortname: bool = True,
    log_args: bool = False,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Декоратор для измерения времени выполнения функции.
    Поддерживает как вызов без аргументов, так и с ключевыми аргументами.
    """

    def actual_decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.perf_counter()
            result = f(*args, **kwargs)
            end = time.perf_counter()

            duration = end - start

            if verbose:
                # if shortname:
                hours_val = "h." if shortname else "hours"
                minute_val = "m." if shortname else "minutes"
                seconds_val = "s." if shortname else "seconds"

                hours = int(duration // 3600)
                minutes = int((duration % 3600) // 60)
                seconds = duration % 60

                time_parts: list[str] = []
                if hours > 0:
                    time_parts.append(f"{hours} {hours_val}")
                if minutes > 0:
                    time_parts.append(f"{minutes} {minute_val}")
                else:
                    time_parts.append(f"0 {minute_val}")

                time_parts.append(f"{seconds:.2f} {seconds_val}")

                message = f"[{f.__name__}] Duration => {' '.join(time_parts)}"

                if log_args and (args or kwargs):
                    message += f" | args={args}, kwargs={kwargs}"

                print(message)

            return result

        return wrapper

    # Определяем, как был вызван декоратор
    if func is None:
        return actual_decorator
    else:
        return actual_decorator(func)


# ---------------------------------------------------- SINGLETON----------------------------------------------------


@overload
def singleton[**P, R](cls: Callable[P, R]) -> Callable[P, R]: ...


@overload
def singleton[**P, R](
    *,
    verbose: bool = True,
    max_instances: int = 1,
    strategy: str = "reuse_last",  # "reuse_last", "reuse_first", "around"
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def singleton[**P, T](
    cls: Callable[P, T] | None = None,
    *,
    verbose: bool = True,
    max_instances: int = 1,
    strategy: str = "reuse_last",
) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Псевдо-singleton декоратор с поддержкой ограниченного количества экземпляров.
    """
    instances: dict[Callable[P, T], deque[T]] = {}
    current_index: dict[Callable[P, T], int] = {}

    def actual_decorator(cls: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(cls)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if cls not in instances:
                instances[cls] = deque(maxlen=max_instances)
                current_index[cls] = 0
            instances_deque = instances[cls]
            if len(instances_deque) < max_instances:
                new_instance = cls(*args, **kwargs)
                instances_deque.append(new_instance)
                if verbose:
                    print(
                        f"Create new instance of {cls.__name__} ({len(instances_deque)}/{max_instances})"
                    )
                return new_instance
            else:
                # Выбираем стратегию повторного использования
                if strategy == "reuse_last":
                    instance = instances_deque[-1]
                elif strategy == "reuse_first":
                    instance = instances_deque[0]
                elif strategy == "around":
                    instance = instances_deque[current_index[cls]]
                    current_index[cls] = (current_index[cls] + 1) % max_instances
                else:
                    instance = instances_deque[-1]  # по умолчанию

                if verbose:
                    print(
                        f"Reuse existing instance of {cls.__name__} ({len(instances_deque)}/{max_instances})"
                    )
                return instance

        return wrapper

    if cls is None:
        return actual_decorator
    return actual_decorator(cls)


# ---------------------------------------------------- SHIT----------------------------------------------------


def handle_errors() -> t:
    """Перехватывает исключения и возвращает значение по умолчанию"""

    def decorator(func: t) -> t:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err = f"⚠️  Error [{func.__name__}]: {e}"
                print(err)
                return err

        return wrapper

    return decorator


def repeat(times: int) -> t:
    """Выполняет функцию несколько раз и возвращает список результатов"""

    def decorator(func: t) -> t:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            results: list[str] = []
            for i in range(times):
                print(f"🔁 Повтор {i + 1}/{times}")
                results.append(func(*args, **kwargs))
            return results

        return wrapper

    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0) -> t:
    """Повторяет вызов функции при ошибках"""

    def decorator(func: t) -> t:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(
                        f"⚠️ Попытка {attempt + 1} не удалась: {e}. Повтор через {delay}с"
                    )
                    if attempt == max_attempts - 1:
                        raise e
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


# ---------------------------------------------------- FILE_CACHE----------------------------------------------------
@overload
def file_cache[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def file_cache[**P, R](
    *,
    verbose: bool = True,
    use_memory: bool = True,
    ttl_seconds: float = 3600,
    auto_create_file: bool = True,
    cache_dir: str = ".cache",
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def file_cache[**P, R](
    func: Callable[P, R] | None = None,
    *,
    verbose: bool = True,
    use_memory: bool = True,
    ttl_seconds: float = 3600,
    auto_create_file: bool = True,
    cache_dir: str = ".cache",
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """Кэширует результаты в файлы"""

    def outer_wrapper(f: Callable[P, R]) -> Callable[P, R]:
        memory_cache: dict[str, Any] = {}
        cache_path = Path(cache_dir)
        if auto_create_file and not cache_path.exists():
            cache_path.mkdir(exist_ok=True, parents=True)

        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal f

            # Создаем ключ кэша
            key_data = f"{f.__module__}.{f.__name__}:{args}:{kwargs}"
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            cache_file = cache_path / f"{key_hash}.pkl"

            if use_memory and key_hash in memory_cache:
                data, timestamp = memory_cache[key_hash]
                if time.time() - timestamp < ttl_seconds:
                    print(f"💾 Использован кэш из памяти для {f.__name__}")

                    # print(f"TTL={ttl_seconds} time-ttl={time.time() - timestamp:2f}")
                    return data

            # Проверяем file cache
            if cache_file.exists():
                if time.time() - cache_file.stat().st_mtime < ttl_seconds:

                    with open(cache_file, "rb") as file:
                        result = pickle.load(file)

                    if use_memory:
                        memory_cache[key_hash] = (result, time.time())
                    if verbose:
                        print(f"♻️  Использован файловый кэш для {f.__name__}")
                    return result

            # Вычисляем и сохраняем
            result = f(*args, **kwargs)

            with open(cache_file, "wb") as file:
                pickle.dump(result, file)

            if use_memory:
                memory_cache[key_hash] = (result, time.time())
            if verbose:
                print(f"💾 Результат закэширован в файл: {cache_file}")
            return result

        return wrapper

    # Определяем, как был вызван декоратор
    if func is None:
        return outer_wrapper
    else:
        return outer_wrapper(func)


# @overload
# def file_cache[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...


# @overload
# def file_cache[**P, R](
#     *,
#     verbose: bool = True,
#     shortname: bool = True,
#     log_args: bool = False,
# ) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


# def file_cache[**P, R](
#     func: Callable[P, R] | None = None,
#     *,
#     verbose: bool = True,
#     shortname: bool = True,
#     log_args: bool = False,
# ) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
#     """
#     Декоратор для измерения времени выполнения функции.
#     Поддерживает как вызов без аргументов, так и с ключевыми аргументами.
#     """

#     def outer_wrapper(f: Callable[P, R]) -> Callable[P, R]:
#         @functools.wraps(f)
#         def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
# nonlocal f
#             result = f(*args, **kwargs)

#             return result

#         return wrapper

#     # Определяем, как был вызван декоратор
#     if func is None:
#         return outer_wrapper
#     else:
#         return outer_wrapper(func)

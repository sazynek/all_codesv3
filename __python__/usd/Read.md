usd -> useful decorator






# from __future__ import annotations
# import functools
# from enum import Enum, auto
# from typing import (
#     Callable,
#     overload,
#     Sequence,
#     Optional,
#     Hashable,
#     TypeAlias,
#     cast,
#     Any,
# )
# import numpy as np
# import pandas as pd
# from toolz import unique as toolz_unique, compose  # type: ignore


# # Типы для данных
# JsonValue: TypeAlias = (
#     str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
# )
# JsonDict: TypeAlias = dict[str, JsonValue]


# class OperationType(Enum):
#     Unique = auto()
#     Slice = auto()
#     Sort = auto()


# class Method(Enum):
#     Toolz = "toolz"
#     Numpy = "numpy"
#     Pandas = "pandas"


# # Конфигурации для операций
# class OperationConfig:
#     pass


# class UniqueConfig(OperationConfig):
#     def __init__(self, key: Optional[Callable[[Any], Hashable]] = None):
#         self.key = key


# class SliceConfig(OperationConfig):
#     def __init__(
#         self,
#         start: Optional[int] = None,
#         stop: Optional[int] = None,
#         step: Optional[int] = None,
#     ):
#         self.start = start
#         self.stop = stop
#         self.step = step


# class SortConfig(OperationConfig):
#     def __init__(
#         self,
#         key: Optional[Callable[[Any], Any]] = None,
#         reverse: bool = False,
#         method: Method = Method.Toolz,
#     ):
#         self.key = key
#         self.reverse = reverse
#         self.method = method


# class ArrayProcessor[T]:
#     """Универсальный процессор с поддержкой multiple операций"""

#     def __init__(self, data: Sequence[T]):
#         self.data = data

#     def process(
#         self,
#         operation: OperationType,
#         config: OperationConfig,
#         method: Method = Method.Toolz,
#     ) -> Sequence[T]:
#         """Основной метод обработки с расширяемой архитектурой"""

#         # Пробуем указанный метод
#         if method != Method.Toolz:
#             try:
#                 return self._try_operation(operation, config, method)
#             except Exception as e:
#                 print(f"⚠️ Запрошенный метод {method} не сработал: {e}")

#         # Автоматический выбор оптимального метода
#         best_method = self._select_optimal_method(operation, config)
#         try:
#             result = self._try_operation(operation, config, best_method)
#             print(f"✅ Автоматически выбран {best_method}")
#             return result
#         except Exception as e:
#             print(f"⚠️ Оптимальный метод {best_method} не сработал: {e}")

#         # Fallback на Toolz
#         return self._try_operation(operation, config, Method.Toolz)

#     def _select_optimal_method(
#         self, operation: OperationType, config: OperationConfig
#     ) -> Method:
#         """Выбирает оптимальный метод для операции"""
#         if not self.data:
#             return Method.Toolz

#         match operation:
#             case OperationType.Unique:
#                 unique_config = cast(UniqueConfig, config)
#                 return self._select_unique_method(unique_config)
#             case OperationType.Slice:
#                 return Method.Toolz  # Slice всегда через Toolz
#             case OperationType.Sort:
#                 sort_config = cast(SortConfig, config)
#                 return self._select_sort_method(sort_config)
#             case _:
#                 return Method.Toolz

#     def _select_unique_method(self, config: UniqueConfig) -> Method:
#         """Выбор метода для уникализации"""
#         if (
#             config.key is None
#             and self.data
#             and self._is_numeric_data()
#             and self._check_numpy_compatibility()
#         ):
#             return Method.Numpy

#         if (
#             self.data
#             and isinstance(self.data[0], dict)
#             and self._check_pandas_compatibility()
#         ):
#             return Method.Pandas

#         return Method.Toolz

#     def _select_sort_method(self, config: SortConfig) -> Method:
#         """Выбор метода для сортировки"""
#         if config.method != Method.Toolz:
#             return config.method

#         if (
#             config.key is None
#             and self.data
#             and self._is_numeric_data()
#             and self._check_numpy_compatibility()
#         ):
#             return Method.Numpy

#         if (
#             self.data
#             and isinstance(self.data[0], dict)
#             and self._check_pandas_compatibility()
#         ):
#             return Method.Pandas

#         return Method.Toolz

#     def _try_operation(
#         self, operation: OperationType, config: OperationConfig, method: Method
#     ) -> Sequence[T]:
#         """Выполняет операцию указанным методом"""
#         match operation:
#             case OperationType.Unique:
#                 unique_config = cast(UniqueConfig, config)
#                 return self._unique(unique_config, method)
#             case OperationType.Slice:
#                 slice_config = cast(SliceConfig, config)
#                 return self._slice(slice_config, method)
#             case OperationType.Sort:
#                 sort_config = cast(SortConfig, config)
#                 return self._sort(sort_config, method)
#             case _:
#                 raise ValueError(f"Неизвестная операция: {operation}")

#     # === UNIQUE OPERATION ===
#     def _unique(self, config: UniqueConfig, method: Method) -> Sequence[T]:
#         match method:
#             case Method.Toolz:
#                 return self._unique_toolz(config.key)
#             case Method.Numpy:
#                 return self._unique_numpy(config.key)
#             case Method.Pandas:
#                 return self._unique_pandas(config.key)
#             case _:
#                 raise ValueError(f"Неизвестный метод для unique: {method}")

#     def _unique_toolz(self, key: Optional[Callable[[T], Hashable]] = None) -> list[T]:
#         unique_iter = (
#             toolz_unique(self.data, key=key) if key else toolz_unique(self.data)
#         )
#         return list(unique_iter)

#     def _unique_numpy(self, key: Optional[Callable[[T], Hashable]] = None) -> list[T]:
#         if key is not None:
#             raise ValueError("NumPy не поддерживает key-функции")
#         if self.data and isinstance(self.data[0], dict):
#             raise ValueError("NumPy не поддерживает словари")

#         arr = np.array(self.data)
#         unique_arr: np.ndarray = np.unique(arr)
#         return unique_arr.tolist()

#     def _unique_pandas(
#         self, key: Optional[Callable[[T], Hashable]] = None
#     ) -> Sequence[T]:
#         if self.data and isinstance(self.data[0], dict):
#             df = pd.DataFrame(self.data)
#             if key is not None:
#                 key_values = [key(item) for item in self.data]
#                 df = (
#                     df.assign(_key=key_values)  # type: ignore
#                     .drop_duplicates(subset=["_key"])
#                     .drop("_key", axis=1)
#                 )
#             else:
#                 df = df.drop_duplicates()
#             return cast(list[T], df.to_dict("records"))  # type: ignore

#         if key is not None:
#             key_series = pd.Series([key(item) for item in self.data])
#             unique_indices = key_series.drop_duplicates().index
#             return [self.data[i] for i in unique_indices]  # type: ignore
#         else:
#             series = pd.Series(self.data)  # type: ignore
#             unique_series = series.drop_duplicates()
#             return cast(list[T], unique_series.tolist())

#     # === SLICE OPERATION ===
#     def _slice(self, config: SliceConfig, method: Method) -> Sequence[T]:
#         match method:
#             case Method.Toolz:
#                 return self._slice_toolz(config)
#             case Method.Numpy:
#                 return self._slice_numpy(config)
#             case Method.Pandas:
#                 return self._slice_pandas(config)
#             case _:
#                 raise ValueError(f"Неизвестный метод для slice: {method}")

#     def _slice_toolz(self, config: SliceConfig) -> list[T]:
#         """Slice с использованием toolz (просто Python slicing)"""
#         return list(self.data[config.start : config.stop : config.step])

#     def _slice_numpy(self, config: SliceConfig) -> list[T]:
#         """Slice с NumPy для числовых данных"""
#         if self.data and isinstance(self.data[0], dict):
#             raise ValueError("NumPy не поддерживает словари для slicing")

#         arr = np.array(self.data)
#         sliced_arr = arr[config.start : config.stop : config.step]
#         return sliced_arr.tolist()

#     def _slice_pandas(self, config: SliceConfig) -> Sequence[T]:
#         """Slice с Pandas"""
#         if self.data and isinstance(self.data[0], dict):
#             df = pd.DataFrame(self.data)
#             sliced_df = df.iloc[config.start : config.stop : config.step]
#             return cast(list[T], sliced_df.to_dict("records"))  # type: ignore
#         else:
#             series = pd.Series(self.data)  # type: ignore
#             sliced_series = series.iloc[config.start : config.stop : config.step]
#             return cast(list[T], sliced_series.tolist())

#     # === SORT OPERATION ===
#     def _sort(self, config: SortConfig, method: Method) -> Sequence[T]:
#         match method:
#             case Method.Toolz:
#                 return self._sort_toolz(config)
#             case Method.Numpy:
#                 return self._sort_numpy(config)
#             case Method.Pandas:
#                 return self._sort_pandas(config)
#             case _:
#                 raise ValueError(f"Неизвестный метод для sort: {method}")

#     def _sort_toolz(self, config: SortConfig) -> list[T]:
#         """Sort с использованием toolz (через sorted)"""

#         if config.key:
#             return sorted(self.data, key=config.key, reverse=config.reverse)
#         else:
#             return sorted(self.data, reverse=config.reverse)  # type: ignore

#     def _sort_numpy(self, config: SortConfig) -> list[T]:
#         """Sort с NumPy"""
#         if config.key is not None:
#             raise ValueError("NumPy не поддерживает key-функции для сортировки")
#         if self.data and isinstance(self.data[0], dict):
#             raise ValueError("NumPy не поддерживает словари для сортировки")

#         arr = np.array(self.data)
#         sorted_indices = np.argsort(arr)
#         if config.reverse:
#             sorted_indices = sorted_indices[::-1]
#         sorted_arr = arr[sorted_indices]
#         return sorted_arr.tolist()

#     def _sort_pandas(self, config: SortConfig) -> Sequence[T]:
#         """Sort с Pandas"""
#         if self.data and isinstance(self.data[0], dict):
#             df = pd.DataFrame(self.data)
#             if config.key:
#                 # Для словарей с key-функцией создаем временную колонку
#                 key_values = [config.key(item) for item in self.data]
#                 df = (
#                     df.assign(_key=key_values)
#                     .sort_values(by="_key", ascending=not config.reverse)
#                     .drop("_key", axis=1)
#                 )
#             else:
#                 df = df.sort_values(by=list(df.columns), ascending=not config.reverse)
#             return cast(list[T], df.to_dict("records"))  # type: ignore
#         else:
#             series = pd.Series(self.data)  # type: ignore
#             if config.key:
#                 key_values = [config.key(item) for item in self.data]
#                 key_series = pd.Series(key_values, index=series.index)
#                 sorted_series = series.iloc[key_series.argsort()]  # type: ignore
#                 if config.reverse:
#                     sorted_series = sorted_series.iloc[::-1]  # type: ignore
#             else:
#                 sorted_series = series.sort_values(ascending=not config.reverse)
#             return cast(list[T], sorted_series.tolist())  # type: ignore

#     # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
#     def _is_numeric_data(self) -> bool:
#         try:
#             return all(isinstance(x, (int, float, np.number)) for x in self.data)
#         except (TypeError, ValueError):
#             return False

#     def _check_numpy_compatibility(self) -> bool:
#         try:
#             np.array(self.data)
#             return True
#         except (ValueError, TypeError):
#             return False

#     def _check_pandas_compatibility(self) -> bool:
#         try:
#             if self.data and isinstance(self.data[0], dict):
#                 pd.DataFrame(self.data)
#             else:
#                 pd.Series(self.data)  # type: ignore
#             return True
#         except (ValueError, TypeError):
#             return False


# def _should_process[U](result: U) -> bool:  # type: ignore
#     """Проверяет, нужно ли обрабатывать результат"""
#     return isinstance(result, Sequence) and not isinstance(result, (str, bytes))


# # === ДЕКОРАТОР UNIQUE ===
# @overload
# def unique[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


# @overload
# def unique[**P, R: Sequence[Any]](
#     *,
#     method: Method = Method.Toolz,
#     key: Optional[Callable[[Any], Hashable]] = None,
# ) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


# def unique[**P, R: Sequence[Any]](
#     func: Callable[P, R] | None = None,
#     method: Method = Method.Toolz,
#     key: Optional[Callable[[Any], Hashable]] = None,
# ) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
#     """Декоратор для уникализации"""

#     def decorator(f: Callable[P, R]) -> Callable[P, R]:
#         @functools.wraps(f)
#         def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
#             result = f(*args, **kwargs)
#             if _should_process(result):
#                 processor = ArrayProcessor(result)
#                 config = UniqueConfig(key=key)
#                 processed = processor.process(
#                     operation=OperationType.Unique,
#                     config=config,
#                     method=method,
#                 )
#                 return cast(R, processed)
#             return result

#         return wrapper

#     if func is None:
#         return decorator
#     else:
#         return decorator(func)


# # === ДЕКОРАТОР SLICE ===
# @overload
# def slice[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


# @overload
# def slice[**P, R: Sequence[Any]](
#     *,
#     start: Optional[int] = None,
#     stop: Optional[int] = None,
#     step: Optional[int] = None,
#     method: Method = Method.Toolz,
# ) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


# def slice[**P, R: Sequence[Any]](
#     func: Callable[P, R] | None = None,
#     start: Optional[int] = None,
#     stop: Optional[int] = None,
#     step: Optional[int] = None,
#     method: Method = Method.Toolz,
# ) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
#     """Декоратор для среза данных"""

#     def decorator(f: Callable[P, R]) -> Callable[P, R]:
#         @functools.wraps(f)
#         def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
#             result = f(*args, **kwargs)
#             if _should_process(result):
#                 processor = ArrayProcessor(result)
#                 config = SliceConfig(start=start, stop=stop, step=step)
#                 processed = processor.process(
#                     operation=OperationType.Slice,
#                     config=config,
#                     method=method,
#                 )
#                 return cast(R, processed)
#             return result

#         return wrapper

#     if func is None:
#         return decorator
#     else:
#         return decorator(func)


# # === ДЕКОРАТОР SORT ===
# @overload
# def sort[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


# @overload
# def sort[**P, R: Sequence[Any]](
#     *,
#     key: Optional[Callable[[Any], Any]] = None,
#     reverse: bool = False,
#     method: Method = Method.Toolz,
# ) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


# def sort[**P, R: Sequence[Any]](
#     func: Callable[P, R] | None = None,
#     key: Optional[Callable[[Any], Any]] = None,
#     reverse: bool = False,
#     method: Method = Method.Toolz,
# ) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
#     """Декоратор для сортировки"""

#     def decorator(f: Callable[P, R]) -> Callable[P, R]:
#         @functools.wraps(f)
#         def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
#             result = f(*args, **kwargs)
#             if _should_process(result):
#                 processor = ArrayProcessor(result)
#                 config = SortConfig(key=key, reverse=reverse, method=method)
#                 processed = processor.process(
#                     operation=OperationType.Sort,
#                     config=config,
#                     method=method,
#                 )
#                 return cast(R, processed)
#             return result

#         return wrapper

#     if func is None:
#         return decorator
#     else:
#         return decorator(func)


# # === ФАБРИКА F ДЛЯ KEY-ФУНКЦИЙ ===
# def F(*field_paths: str) -> Callable[[JsonDict], Hashable]:
#     """Фабрика key-функций с поддержкой нескольких полей"""

#     def _get_nested_value(item: JsonDict, field_path: str) -> JsonValue:
#         keys = field_path.split(".")
#         current: JsonValue = item
#         for key in keys:
#             if isinstance(current, dict) and key in current:
#                 current = current[key]
#             else:
#                 raise KeyError(f"Поле '{key}' не найдено по пути '{field_path}'")

#         if not isinstance(current, (str, int, float, bool, type(None))):
#             raise TypeError(
#                 f"Значение по пути '{field_path}' не хешируемо: {type(current)}"
#             )

#         return current

#     def key_func(item: JsonDict) -> Hashable:
#         if len(field_paths) == 1:
#             value = _get_nested_value(item, field_paths[0])
#             return cast(Hashable, value)
#         else:
#             values = tuple(_get_nested_value(item, path) for path in field_paths)
#             return cast(Hashable, values)

#     return key_func


# # === ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ===
# @unique
# def get_numeric_data() -> list[int]:
#     return [1, 2, 2, 3, 4, 4, 5, 1]


# @unique(key=F("id", "name.gg"))
# def get_dict_data() -> list[JsonDict]:
#     return [
#         {"id": 1, "name": {"gg": "Alice"}},
#         {"id": 2, "name": {"gg": "Alice"}},
#         {"id": 1, "name": {"gg": "G"}},
#         {"id": 1, "name": {"gg": "Alice"}},
#         {"id": 3, "name": {"gg": "G"}},
#     ]


# @slice(start=1, stop=4, method=Method.Pandas)
# def get_sliced_data() -> list[int]:
#     return [10, 20, 30, 40, 50]


# @sort(key=F("id"), reverse=True, method=Method.Pandas)
# def get_sorted_data() -> list[JsonDict]:
#     return [
#         {"id": 1, "name": "Alice"},
#         {"id": 3, "name": "Charlie"},
#         {"id": 2, "name": "Bob"},
#     ]


# if __name__ == "__main__":
#     print("🔢 Числа (unique):", get_numeric_data())
#     print("📊 Словари (unique):", get_dict_data())
#     print("✂️ Срез (slice):", get_sliced_data())
#     print("📈 Сортировка (sort):", get_sorted_data())

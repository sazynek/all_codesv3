from __future__ import annotations
import functools
from enum import Enum, auto
from typing import (
    Callable,
    overload,
    Sequence,
    Optional,
    Hashable,
    TypeAlias,
    cast,
    Any,
    Iterator,
    # Iterable,
)
from toolz import (  # type: ignore
    unique as toolz_unique,  # type: ignore
    groupby as toolz_groupby,  # type: ignore
    take as toolz_take,  # type: ignore
    drop as toolz_drop,  # type: ignore
    partition_all,  # type: ignore
    concat,  # type: ignore
    compose,  # type: ignore
    pipe,  # type: ignore
    interpose as toolz_interpose,  # type: ignore
    pluck as toolz_pluck,  # type: ignore
    diff as toolz_diff,  # type: ignore
    topk as toolz_topk,  # type: ignore
    remove as toolz_remove,  # type: ignore
    accumulate as toolz_accumulate,  # type: ignore
    join as toolz_join,  # type: ignore
)


# Типы для данных
JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
)
JsonDict: TypeAlias = dict[str, JsonValue]


class OperationType(Enum):
    Unique = auto()
    Slice = auto()
    Sort = auto()
    Filter = auto()
    Map = auto()
    GroupBy = auto()
    Flatten = auto()
    Chunk = auto()
    Take = auto()
    Drop = auto()
    Interpose = auto()
    Pluck = auto()
    Diff = auto()
    TopK = auto()
    Remove = auto()
    Accumulate = auto()
    Join = auto()


# Конфигурации для операций
class OperationConfig:
    pass


class UniqueConfig(OperationConfig):
    def __init__(self, key: Optional[Callable[[Any], Hashable]] = None):
        self.key = key


class SliceConfig(OperationConfig):
    def __init__(
        self,
        start: Optional[int] = None,
        stop: Optional[int] = None,
        step: Optional[int] = None,
    ):
        self.start = start
        self.stop = stop
        self.step = step


class SortConfig(OperationConfig):
    def __init__(
        self,
        key: Optional[Callable[[Any], Any]] = None,
        reverse: bool = False,
    ):
        self.key = key
        self.reverse = reverse


class FilterConfig(OperationConfig):
    def __init__(self, predicate: Callable[[Any], bool]):
        self.predicate = predicate


class MapConfig(OperationConfig):
    def __init__(self, transform: Callable[[Any], Any]):
        self.transform = transform


class GroupByConfig(OperationConfig):
    def __init__(self, key: Callable[[Any], Hashable]):
        self.key = key


class FlattenConfig(OperationConfig):
    def __init__(self, level: int = 1):
        self.level = level


class ChunkConfig(OperationConfig):
    def __init__(self, size: int):
        self.size = size


class TakeConfig(OperationConfig):
    def __init__(self, n: int):
        self.n = n


class DropConfig(OperationConfig):
    def __init__(self, n: int):
        self.n = n


class InterposeConfig(OperationConfig):
    def __init__(self, separator: Any):
        self.separator = separator


class PluckConfig(OperationConfig):
    def __init__(self, key: str | int | Sequence[str | int]):
        self.key = key


class DiffConfig(OperationConfig):
    def __init__(self, default: Any = None):
        self.default = default


class TopKConfig(OperationConfig):
    def __init__(self, k: int, key: Optional[Callable[[Any], Any]] = None):
        self.k = k
        self.key = key


class RemoveConfig(OperationConfig):
    def __init__(self, predicate: Callable[[Any], bool]):
        self.predicate = predicate


class AccumulateConfig(OperationConfig):
    def __init__(self, func: Callable[[Any, Any], Any], initial: Optional[Any] = None):
        self.func = func
        self.initial = initial


class JoinConfig(OperationConfig):
    def __init__(
        self,
        left_key: Callable[[Any], Hashable],
        right_data: Sequence[Any],
        right_key: Callable[[Any], Hashable],
    ):
        self.left_key = left_key
        self.right_data = right_data
        self.right_key = right_key


class ArrayProcessor[T]:
    """Универсальный процессор на основе Toolz"""

    def __init__(self, data: Sequence[T]):
        self.data = data

    def process(
        self,
        operation: OperationType,
        config: OperationConfig,
    ) -> Sequence[T] | dict[Hashable, list[T]]:
        """Основной метод обработки"""
        return self._try_operation(operation, config)

    def _try_operation(
        self, operation: OperationType, config: OperationConfig
    ) -> Sequence[T] | dict[Hashable, list[T]]:
        match operation:
            case OperationType.Unique:
                unique_config = cast(UniqueConfig, config)
                return self._unique(unique_config)
            case OperationType.Slice:
                slice_config = cast(SliceConfig, config)
                return self._slice(slice_config)
            case OperationType.Sort:
                sort_config = cast(SortConfig, config)
                return self._sort(sort_config)
            case OperationType.Filter:
                filter_config = cast(FilterConfig, config)
                return self._filter(filter_config)
            case OperationType.Map:
                map_config = cast(MapConfig, config)
                return self._map(map_config)
            case OperationType.GroupBy:
                group_config = cast(GroupByConfig, config)
                return self._groupby(group_config)
            case OperationType.Flatten:
                flatten_config = cast(FlattenConfig, config)
                return self._flatten(flatten_config)
            case OperationType.Chunk:
                chunk_config = cast(ChunkConfig, config)
                return self._chunk(chunk_config)  # type: ignore
            case OperationType.Take:
                take_config = cast(TakeConfig, config)
                return self._take(take_config)
            case OperationType.Drop:
                drop_config = cast(DropConfig, config)
                return self._drop(drop_config)
            case OperationType.Interpose:
                interpose_config = cast(InterposeConfig, config)
                return self._interpose(interpose_config)
            case OperationType.Pluck:
                pluck_config = cast(PluckConfig, config)
                return self._pluck(pluck_config)
            case OperationType.Diff:
                diff_config = cast(DiffConfig, config)
                return self._diff(diff_config)
            case OperationType.TopK:
                topk_config = cast(TopKConfig, config)
                return self._topk(topk_config)
            case OperationType.Remove:
                remove_config = cast(RemoveConfig, config)
                return self._remove(remove_config)
            case OperationType.Accumulate:
                accumulate_config = cast(AccumulateConfig, config)
                return self._accumulate(accumulate_config)
            case OperationType.Join:
                join_config = cast(JoinConfig, config)
                return self._join(join_config)
            case _:
                raise ValueError(f"Неизвестная операция: {operation}")

    # === UNIQUE OPERATION ===
    def _unique(self, config: UniqueConfig) -> Sequence[T]:
        return self._unique_toolz(config.key)

    def _unique_toolz(self, key: Optional[Callable[[T], Hashable]] = None) -> list[T]:
        try:
            # Пробуем использовать toolz.unique
            unique_iter = (
                toolz_unique(self.data, key=key) if key else toolz_unique(self.data)
            )
            return list(unique_iter)
        except TypeError as e:
            if "unhashable type" in str(e):
                # Если элементы нехэшируемы и key не указан, используем альтернативный подход
                if key is None:
                    return self._unique_fallback()
                else:
                    raise
            else:
                raise

    def _unique_fallback(self) -> list[T]:
        """Альтернативная реализация для нехэшируемых типов"""
        seen = []
        result = []
        for item in self.data:
            # Для нехэшируемых типов используем сравнение через repr или прямой поиск
            item_repr = repr(item)
            if item_repr not in seen:
                seen.append(item_repr)  # type: ignore
                result.append(item)  # type: ignore
        return result  # type: ignore

    # === SLICE OPERATION ===
    def _slice(self, config: SliceConfig) -> Sequence[T]:
        return self._slice_toolz(config)

    def _slice_toolz(self, config: SliceConfig) -> list[T]:
        return list(self.data[config.start : config.stop : config.step])

    # === SORT OPERATION ===
    def _sort(self, config: SortConfig) -> Sequence[T]:
        return self._sort_toolz(config)

    def _sort_toolz(self, config: SortConfig) -> list[T]:
        if config.key:
            return sorted(self.data, key=config.key, reverse=config.reverse)
        else:
            return sorted(self.data, reverse=config.reverse)  # type: ignore

    # === FILTER OPERATION ===
    def _filter(self, config: FilterConfig) -> Sequence[T]:
        return self._filter_toolz(config)

    def _filter_toolz(self, config: FilterConfig) -> list[T]:
        return [item for item in self.data if config.predicate(item)]

    # === MAP OPERATION ===
    def _map(self, config: MapConfig) -> Sequence[Any]:
        return self._map_toolz(config)

    def _map_toolz(self, config: MapConfig) -> list[Any]:
        return [config.transform(item) for item in self.data]

    # === GROUPBY OPERATION ===
    def _groupby(self, config: GroupByConfig) -> dict[Hashable, list[T]]:
        return self._groupby_toolz(config)

    def _groupby_toolz(self, config: GroupByConfig) -> dict[Hashable, list[T]]:
        return toolz_groupby(config.key, self.data)  # type: ignore

    # === FLATTEN OPERATION ===
    def _flatten(self, config: FlattenConfig) -> Sequence[Any]:
        return self._flatten_toolz(config)

    def _flatten_toolz(self, config: FlattenConfig) -> list[Any]:
        def _flatten_deep(items: Sequence[Any], level: int) -> Iterator[Any]:
            """Рекурсивное выравнивание с контролем уровня"""
            if level <= 0:
                yield from items
                return

            for item in items:
                if isinstance(item, (list, tuple)):
                    yield from _flatten_deep(item, level - 1)  # type: ignore
                else:
                    yield item

        return list(_flatten_deep(self.data, config.level))

    # === CHUNK OPERATION ===
    def _chunk(self, config: ChunkConfig) -> Sequence[list[T]]:
        return self._chunk_toolz(config)

    def _chunk_toolz(self, config: ChunkConfig) -> list[list[T]]:
        return list(partition_all(config.size, self.data))  # type: ignore

    # === TAKE OPERATION ===
    def _take(self, config: TakeConfig) -> Sequence[T]:
        return self._take_toolz(config)

    def _take_toolz(self, config: TakeConfig) -> list[T]:
        return list(toolz_take(config.n, self.data))  # type: ignore

    # === DROP OPERATION ===
    def _drop(self, config: DropConfig) -> Sequence[T]:
        return self._drop_toolz(config)

    def _drop_toolz(self, config: DropConfig) -> list[T]:
        return list(toolz_drop(config.n, self.data))

    # === INTERPOSE OPERATION ===
    def _interpose(self, config: InterposeConfig) -> Sequence[Any]:
        return self._interpose_toolz(config)

    def _interpose_toolz(self, config: InterposeConfig) -> list[Any]:
        """Вставляет разделитель между элементами"""
        return list(toolz_interpose(config.separator, self.data))  # type: ignore

    # === PLUCK OPERATION ===
    def _pluck(self, config: PluckConfig) -> Sequence[Any]:
        return self._pluck_toolz(config)

    def _pluck_toolz(self, config: PluckConfig) -> list[Any]:
        """Извлекает значения по ключу из словарей или элементов"""
        if isinstance(config.key, (str, int)):
            return list(toolz_pluck(config.key, self.data))  # type: ignore
        else:
            return list(toolz_pluck(config.key, self.data))  # type: ignore

    # === DIFF OPERATION ===
    def _diff(self, config: DiffConfig) -> Sequence[Any]:
        return self._diff_toolz(config)

    def _diff_toolz(self, config: DiffConfig) -> Sequence[Any]:
        """Вычисляет разницу между последовательными элементами"""
        if len(self.data) <= 1:
            return []

        result = []
        for i in range(1, len(self.data)):
            diff = (  # type: ignore
                self.data[i] - self.data[i - 1]  # type: ignore
            )  # предполагая, что элементы поддерживают вычитание
            result.append(diff)  # type: ignore

        return result  # type: ignore

    # === TOPK OPERATION ===
    def _topk(self, config: TopKConfig) -> Sequence[T]:
        return self._topk_toolz(config)

    def _topk_toolz(self, config: TopKConfig) -> list[T]:
        """Возвращает k наибольших элементов"""
        if config.key:
            return list(toolz_topk(config.k, self.data, key=config.key))
        else:
            return list(toolz_topk(config.k, self.data))

    # === REMOVE OPERATION ===
    def _remove(self, config: RemoveConfig) -> Sequence[T]:
        return self._remove_toolz(config)

    def _remove_toolz(self, config: RemoveConfig) -> list[T]:
        """Удаляет элементы, удовлетворяющие предикату"""
        return list(toolz_remove(config.predicate, self.data))

    # === ACCUMULATE OPERATION ===
    def _accumulate(self, config: AccumulateConfig) -> Sequence[Any]:
        return self._accumulate_toolz(config)

    def _accumulate_toolz(self, config: AccumulateConfig) -> list[Any]:
        """Накопительное применение функции"""
        if config.initial is not None:
            return list(toolz_accumulate(config.func, self.data, config.initial))  # type: ignore
        else:
            return list(toolz_accumulate(config.func, self.data))  # type: ignore

    # === JOIN OPERATION ===
    def _join(self, config: JoinConfig) -> Sequence[Any]:
        return self._join_toolz(config)

    def _join_toolz(self, config: JoinConfig) -> list[Any]:
        """Объединение двух последовательностей по ключу"""
        return list(
            toolz_join(config.left_key, self.data, config.right_key, config.right_data)  # type: ignore
        )


def _should_process[U](result: U) -> bool:  # type: ignore
    return isinstance(result, Sequence) and not isinstance(result, (str, bytes))


# === ДЕКОРАТОР UNIQUE ===
@overload
def unique[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def unique[**P, R: Sequence[Any]](
    *,
    key: Optional[Callable[[Any], Hashable]] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def unique[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    key: Optional[Callable[[Any], Hashable]] = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result):
                processor = ArrayProcessor(result)
                config = UniqueConfig(key=key)
                processed = processor.process(
                    operation=OperationType.Unique,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР SLICE ===
@overload
def slice[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def slice[**P, R: Sequence[Any]](
    *,
    start: Optional[int] = None,
    stop: Optional[int] = None,
    step: Optional[int] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def slice[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    start: Optional[int] = None,
    stop: Optional[int] = None,
    step: Optional[int] = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result):
                processor = ArrayProcessor(result)
                config = SliceConfig(start=start, stop=stop, step=step)
                processed = processor.process(
                    operation=OperationType.Slice,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР SORT ===
@overload
def sort[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def sort[**P, R: Sequence[Any]](
    *,
    key: Optional[Callable[[Any], Any]] = None,
    reverse: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def sort[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    key: Optional[Callable[[Any], Any]] = None,
    reverse: bool = False,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result):
                processor = ArrayProcessor(result)
                config = SortConfig(key=key, reverse=reverse)
                processed = processor.process(
                    operation=OperationType.Sort,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР FILTER ===
@overload
def filter[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def filter[**P, R: Sequence[Any]](
    *,
    predicate: Callable[[Any], bool],
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def filter[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    predicate: Callable[[Any], bool] | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result) and predicate:
                processor = ArrayProcessor(result)
                config = FilterConfig(predicate=predicate)
                processed = processor.process(
                    operation=OperationType.Filter,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР MAP ===
@overload
def map[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def map[**P, R: Sequence[Any]](
    *,
    transform: Callable[[Any], Any],
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def map[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    transform: Callable[[Any], Any] | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result) and transform:
                processor = ArrayProcessor(result)
                config = MapConfig(transform=transform)
                processed = processor.process(
                    operation=OperationType.Map,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР GROUPBY ===
@overload
def groupby[**P, R: Sequence[Any]](
    func: Callable[P, R],
) -> Callable[P, dict[Hashable, list[Any]]]: ...


@overload
def groupby[**P](
    *,
    key: Callable[[Any], Hashable],
) -> Callable[[Callable[P, Sequence[Any]]], Callable[P, dict[Hashable, list[Any]]]]: ...


def groupby[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    key: Callable[[Any], Hashable] | None = None,
) -> (
    Callable[P, dict[Hashable, list[Any]]]
    | Callable[[Callable[P, R]], Callable[P, dict[Hashable, list[Any]]]]
):
    def decorator(f: Callable[P, R]) -> Callable[P, dict[Hashable, list[Any]]]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> dict[Hashable, list[Any]]:
            result = f(*args, **kwargs)
            if _should_process(result) and key:
                processor = ArrayProcessor(result)
                config = GroupByConfig(key=key)
                processed = processor.process(
                    operation=OperationType.GroupBy,
                    config=config,
                )
                return cast(dict[Hashable, list[Any]], processed)
            return {}  # type: ignore

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР FLATTEN ===
@overload
def flatten[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def flatten[**P, R: Sequence[Any]](
    *,
    level: int = 1,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def flatten[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    level: int = 1,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result):
                processor = ArrayProcessor(result)
                config = FlattenConfig(level=level)
                processed = processor.process(
                    operation=OperationType.Flatten,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР CHUNK ===
@overload
def chunk[**P, R: Sequence[Any]](
    func: Callable[P, R],
) -> Callable[P, list[list[Any]]]: ...


@overload
def chunk[**P](
    *,
    size: int,
) -> Callable[[Callable[P, Sequence[Any]]], Callable[P, list[list[Any]]]]: ...


def chunk[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    size: int | None = None,
) -> (
    Callable[P, list[list[Any]]]
    | Callable[[Callable[P, R]], Callable[P, list[list[Any]]]]
):
    def decorator(f: Callable[P, R]) -> Callable[P, list[list[Any]]]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[list[Any]]:
            result = f(*args, **kwargs)
            if _should_process(result) and size:
                processor = ArrayProcessor(result)
                config = ChunkConfig(size=size)
                processed = processor.process(
                    operation=OperationType.Chunk,
                    config=config,
                )
                return cast(list[list[Any]], processed)
            return []  # type: ignore

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР TAKE ===
@overload
def take[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def take[**P, R: Sequence[Any]](
    *,
    n: int,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def take[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    n: int | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result) and n is not None:
                processor = ArrayProcessor(result)
                config = TakeConfig(n=n)
                processed = processor.process(
                    operation=OperationType.Take,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР DROP ===
@overload
def drop[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def drop[**P, R: Sequence[Any]](
    *,
    n: int,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def drop[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    n: int | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result) and n is not None:
                processor = ArrayProcessor(result)
                config = DropConfig(n=n)
                processed = processor.process(
                    operation=OperationType.Drop,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР INTERPOSE ===
@overload
def interpose[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def interpose[**P, R: Sequence[Any]](
    *,
    separator: Any,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def interpose[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    separator: Any | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result) and separator is not None:
                processor = ArrayProcessor(result)
                config = InterposeConfig(separator=separator)
                processed = processor.process(
                    operation=OperationType.Interpose,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР PLUCK ===
@overload
def pluck[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def pluck[**P, R: Sequence[Any]](
    *,
    key: str | int | Sequence[str | int],
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def pluck[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    key: str | int | Sequence[str | int] | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result) and key is not None:
                processor = ArrayProcessor(result)
                config = PluckConfig(key=key)
                processed = processor.process(
                    operation=OperationType.Pluck,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР DIFF ===
@overload
def diff[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def diff[**P, R: Sequence[Any]](
    *,
    default: Any = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def diff[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    default: Any | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result):
                processor = ArrayProcessor(result)
                config = DiffConfig(default=default)
                processed = processor.process(
                    operation=OperationType.Diff,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР TOPK ===
@overload
def topk[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def topk[**P, R: Sequence[Any]](
    *,
    k: int,
    key: Optional[Callable[[Any], Any]] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def topk[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    k: int | None = None,
    key: Optional[Callable[[Any], Any]] = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result) and k is not None:
                processor = ArrayProcessor(result)
                config = TopKConfig(k=k, key=key)
                processed = processor.process(
                    operation=OperationType.TopK,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР REMOVE ===
@overload
def remove[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def remove[**P, R: Sequence[Any]](
    *,
    predicate: Callable[[Any], bool],
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def remove[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    predicate: Callable[[Any], bool] | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result) and predicate:
                processor = ArrayProcessor(result)
                config = RemoveConfig(predicate=predicate)
                processed = processor.process(
                    operation=OperationType.Remove,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ДЕКОРАТОР ACCUMULATE ===
# === ДЕКОРАТОР ACCUMULATE ===
@overload
def accumulate[**P, R: Sequence[Any]](func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def accumulate[**P, R: Sequence[Any]](
    *,
    func: Callable[[Any, Any], Any],  # Сохраняем оригинальное имя в API
    initial: Optional[Any] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def accumulate[**P, R: Sequence[Any]](  # type: ignore
    decorated_func: Callable[P, R] | None = None,  # Переименовываем первый параметр
    *,
    func: Callable[..., Any] | None = None,
    initial: Optional[Any] = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = f(*args, **kwargs)
            if _should_process(result) and func is not None:
                processor = ArrayProcessor(result)
                config = AccumulateConfig(func=func, initial=initial)
                processed = processor.process(
                    operation=OperationType.Accumulate,
                    config=config,
                )
                return cast(R, processed)
            return result

        return wrapper

    if decorated_func is None:  # Используем переименованный параметр
        return decorator
    else:
        return decorator(decorated_func)  # Используем переименованный параметр


# === ДЕКОРАТОР JOIN ===
@overload
def join[**P, R: Sequence[Any]](
    func: Callable[P, R],
) -> Callable[P, list[Any]]: ...


@overload
def join[**P, R: Sequence[Any]](
    *,
    left_key: Callable[[Any], Hashable],
    right_data: Sequence[Any],
    right_key: Callable[[Any], Hashable],
) -> Callable[[Callable[P, R]], Callable[P, list[Any]]]: ...  # type: ignore


def join[**P, R: Sequence[Any]](
    func: Callable[P, R] | None = None,
    left_key: Callable[[Any], Hashable] | None = None,
    right_data: Sequence[Any] | None = None,
    right_key: Callable[[Any], Hashable] | None = None,
) -> Callable[P, list[Any]] | Callable[[Callable[P, R]], Callable[P, list[Any]]]:
    def decorator(f: Callable[P, R]) -> Callable[P, list[Any]]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[Any]:
            result = f(*args, **kwargs)
            if (
                _should_process(result)
                and left_key is not None
                and right_data is not None
                and right_key is not None
            ):
                processor = ArrayProcessor(result)
                config = JoinConfig(
                    left_key=left_key, right_data=right_data, right_key=right_key
                )
                processed = processor.process(
                    operation=OperationType.Join,
                    config=config,
                )
                return cast(list[Any], processed)
            return []  # type: ignore

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


# === ФАБРИКА F ДЛЯ KEY-ФУНКЦИЙ ===
def F(*field_paths: str) -> Callable[[JsonDict], Hashable]:
    def _get_nested_value(item: JsonDict, field_path: str) -> JsonValue:
        keys = field_path.split(".")
        current: JsonValue = item
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None  # Возвращаем None вместо исключения для большей гибкости
        return current

    def key_func(item: JsonDict) -> Hashable:
        if len(field_paths) == 1:
            value = _get_nested_value(item, field_paths[0])
            return cast(Hashable, value)
        else:
            values = tuple(_get_nested_value(item, path) for path in field_paths)
            return cast(Hashable, values)

    return key_func

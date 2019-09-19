import typing

T = typing.TypeVar("T")
DependableFunc = typing.Union[
    typing.Callable[..., typing.Awaitable[T]],
    typing.Callable[..., typing.AsyncContextManager[T]],
]
F = typing.TypeVar("F", bound=DependableFunc)


class Dependable(typing.Generic[T]):
    __slots__ = ("func", "cached")

    def __init__(self, func: DependableFunc[T], cached: bool = None) -> None:
        self.func = func
        self.cached = cached

    def __eq__(self, other: typing.Any) -> bool:
        if not isinstance(other, Dependable):
            return False
        return self.func == other.func and self.cached == other.cached

    def __hash__(self) -> int:
        return hash((self.func, self.cached))

    def __repr__(self) -> str:
        attrs = [f"func={self.func!r}"]
        if self.cached:
            attrs.append("cached")
        return f"{self.__class__.__name__}({', '.join(attrs)})"


class DependablesCache(typing.Mapping[Dependable, typing.Any]):
    def __init__(self) -> None:
        self._last_id = 0
        self._cached_dependables: typing.Dict[Dependable, typing.Any] = {}
        self._cachable_funcs: typing.Set[DependableFunc] = set()

    def __getitem__(self, dep: Dependable[T]) -> T:
        return self._cached_dependables[dep]

    def __setitem__(self, dep: Dependable[T], value: T) -> None:
        self._cached_dependables[dep] = value

    def __len__(self) -> int:
        return len(self._cached_dependables)

    def __iter__(self) -> typing.Iterator[Dependable]:
        return iter(self._cached_dependables)

    def should_cache(self, dep: Dependable[T]) -> bool:
        if dep.cached:
            return dep not in self
        if dep.cached is None:
            # 'cached=...' was not passed to 'depends()'.
            # => Should cache if the dependable function was decorated with '@cached'
            return dep.func in self._cachable_funcs
        return False

    def cached(self, func: F) -> F:
        self._cachable_funcs.add(func)
        return func

    def clear(self) -> None:
        self._cached_dependables = {}
        self._cachable_funcs = set()


cache = DependablesCache()

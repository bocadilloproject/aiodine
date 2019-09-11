import inspect
import typing

T = typing.TypeVar("T")
DependableFunc = typing.Callable[..., typing.Awaitable[T]]


def depends(func: DependableFunc[T]) -> T:
    return typing.cast(T, Dependable(func))


class Dependable(typing.Generic[T]):
    def __init__(self, func: DependableFunc[T]):
        self.func = func

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(func={self.func!r})"


async def call_resolved(
    func: DependableFunc[T], *args: typing.Any, **kwargs: typing.Any
) -> typing.T:
    signature = inspect.signature(func)

    if not signature.parameters:
        return await func(*args, **kwargs)

    bound = signature.bind_partial(*args, **kwargs)
    bound.apply_defaults()

    for name, value in bound.arguments.items():
        if isinstance(value, Dependable):
            bound.arguments[name] = await call_resolved(value.func)

    return await func(*bound.args, **bound.kwargs)

import inspect
import types
import typing

from .compat import (
    AsyncExitStack,
    asynccontextmanager,
    asyncnullcontext,
    is_async_context_manager,
)

T = typing.TypeVar("T")
DependableFunc = typing.Union[
    typing.Callable[..., typing.Awaitable[T]],
    typing.Callable[..., typing.AsyncContextManager[T]],
]


def depends(func: DependableFunc[T]) -> T:
    return typing.cast(T, Dependable(func))


class Dependable(typing.Generic[T]):
    def __init__(self, func: DependableFunc[T]):
        self.func = func

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(func={self.func!r})"


async def call_resolved(
    func: DependableFunc[T],
    *args: typing.Any,
    __exit_stack__: AsyncExitStack = None,
    **kwargs: typing.Any,
) -> T:
    if __exit_stack__ is None:
        is_sub_dependency = False
        exit_stack = AsyncExitStack()
    else:
        is_sub_dependency = True
        exit_stack = __exit_stack__

    signature = inspect.signature(func)

    bound = signature.bind_partial(*args, **kwargs)
    bound.apply_defaults()

    for name, value in bound.arguments.items():
        if isinstance(value, Dependable):
            bound.arguments[name] = await call_resolved(
                value.func, __exit_stack__=exit_stack
            )

    raw = func(*bound.args, **bound.kwargs)

    ctx = (
        exit_stack
        if not is_sub_dependency
        else typing.cast(typing.AsyncContextManager, asyncnullcontext())
    )

    async with ctx:
        if isinstance(raw, types.CoroutineType):
            return await raw
        elif is_async_context_manager(raw):
            raw = typing.cast(typing.AsyncContextManager[T], raw)
            return await exit_stack.enter_async_context(raw)
        else:
            raise ValueError(
                f"Expected coroutine or async context manager, got {type(raw)!r}"
            )

import inspect
import types
import typing

from .compat import (
    AsyncExitStack,
    asynccontextmanager,
    asyncnullcontext,
    is_async_context_manager,
)
from .models import Dependable, DependableFunc, DependablesCache, T


def depends(func: DependableFunc[T], *, cached: bool = None) -> T:
    return typing.cast(T, Dependable(func, cached=cached))


CACHE = DependablesCache()


async def call_resolved(
    func: DependableFunc[T],
    *args: typing.Any,
    __exit_stack__: AsyncExitStack = None,
    **kwargs: typing.Any,
) -> T:
    if __exit_stack__ is None:
        is_root_call = True
        exit_stack = AsyncExitStack()
    else:
        is_root_call = False
        exit_stack = __exit_stack__

    signature = inspect.signature(func)

    bound = signature.bind_partial(*args, **kwargs)
    bound.apply_defaults()

    for name, val in bound.arguments.items():
        if isinstance(val, Dependable):
            dependable = val

            try:
                value = CACHE[dependable]
            except KeyError:
                value = await call_resolved(dependable.func, __exit_stack__=exit_stack)
                if CACHE.should_cache(dependable):
                    CACHE[dependable] = value

            bound.arguments[name] = value

    ctx = (
        exit_stack
        if is_root_call
        else typing.cast(typing.AsyncContextManager, asyncnullcontext())
    )

    async with ctx:
        raw = func(*bound.args, **bound.kwargs)

        if isinstance(raw, types.CoroutineType):
            return await raw

        if is_async_context_manager(raw):
            raw = typing.cast(typing.AsyncContextManager[T], raw)
            return await exit_stack.enter_async_context(raw)

        raise ValueError(
            f"Expected coroutine or async context manager, got {type(raw)!r}"
        )

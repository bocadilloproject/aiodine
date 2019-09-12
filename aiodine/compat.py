import inspect
import typing

try:
    from contextlib import (
        AsyncExitStack,
        asynccontextmanager,
        AbstractAsyncContextManager,
    )
except ImportError:  # pragma: no cover
    AbstractAsyncContextManager = None  # type: ignore
    from async_generator import asynccontextmanager  # type: ignore
    from async_exit_stack import AsyncExitStack  # type: ignore


def is_async_context_manager(obj: typing.Any) -> bool:
    if AbstractAsyncContextManager is None:  # pragma: no cover
        return (
            not inspect.isclass(obj)
            and hasattr(obj, "__aenter__")
            and hasattr(obj, "__aexit__")
        )
    return isinstance(obj, AbstractAsyncContextManager)


class asyncnullcontext:
    async def __aenter__(self) -> None:
        pass

    async def __aexit__(self, *args: typing.Any) -> None:
        pass

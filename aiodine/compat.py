import sys

from functools import wraps
from typing import AsyncGenerator, Awaitable, Callable, Generator

try:  # pragma: no cover
    from contextlib import AsyncExitStack  # pylint: disable=unused-import
except ImportError:  # pragma: no cover
    from async_exit_stack import AsyncExitStack


if sys.version_info < (3, 7):  # pragma: no cover
    from aiocontextvars import (  # pylint: disable=unused-import, import-error
        ContextVar,
        Token,
    )
else:  # pragma: no cover
    from contextvars import ContextVar, Token  # pylint: disable=unused-import


def wrap_async(func: Callable) -> Callable[..., Awaitable]:
    @wraps(func)
    async def async_func(*args, **kwargs):
        return func(*args, **kwargs)

    return async_func


def wrap_generator_async(gen: Generator) -> Callable[..., AsyncGenerator]:
    @wraps(gen)
    async def async_gen(*args, **kwargs):
        for item in gen(*args, **kwargs):
            yield item

    return async_gen

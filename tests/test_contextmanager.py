import typing
from contextlib import nullcontext

import anyio
import pytest
import sniffio

import aiodine
from aiodine.compat import asynccontextmanager


@pytest.mark.anyio
async def test_call_contextmanager() -> None:
    event = anyio.create_event()

    @asynccontextmanager
    async def moo() -> typing.AsyncIterator[str]:
        yield "moo"
        await event.set()

    await aiodine.call_resolved(moo) == "moo"
    assert event.is_set()


@pytest.mark.anyio
@pytest.mark.parametrize("should_raise", (False, True))
@pytest.mark.parametrize("use_finally", (False, True))
async def test_depend_on_contextmanager(should_raise: bool, use_finally: bool) -> None:
    if sniffio.current_async_library() == "curio" and use_finally:
        pytest.xfail(
            "curio currently disallows async code in 'finally' block "
            "of vanilla async generator"
        )

    event = anyio.create_event()

    if use_finally:

        @asynccontextmanager
        async def moo() -> typing.AsyncIterator[str]:
            try:
                yield "moo"
            finally:
                await event.set()

    else:

        @asynccontextmanager
        async def moo() -> typing.AsyncIterator[str]:
            yield "moo"
            await event.set()

    async def say(who: str, what: str = aiodine.depends(moo)) -> str:
        if should_raise:
            raise ValueError
        return f"{who} says {what}"

    with pytest.raises(ValueError) if should_raise else nullcontext():
        await aiodine.call_resolved(say, "cow") == "cow says moo"

    should_cleanup = use_finally or not should_raise
    assert event.is_set() if should_cleanup else not event.is_set()


@pytest.mark.anyio
@pytest.mark.parametrize("should_raise", (True, False))
async def depend_on_class_style_contextmanager(should_raise: bool) -> None:
    event = anyio.create_event()

    class Moo:
        async def __aenter__(self) -> str:
            return "moo"

        async def __aexit__(
            self,
            exc_type: typing.Optional[typing.Type[BaseException]],
            *args: typing.Any,
        ) -> typing.Optional[bool]:
            await event.set()
            return True if exc_type is not None else None

    async def say(who: str, what: str = aiodine.depends(Moo)) -> str:
        if should_raise:
            raise ValueError
        return f"{who} says {what}"

    with pytest.raises(ValueError) if should_raise else nullcontext():
        await aiodine.call_resolved(say, "cow") == "cow says moo"

    assert event.is_set()


@pytest.mark.anyio
async def test_plain_async_generator_not_supported() -> None:
    async def moo() -> typing.AsyncIterator[str]:
        yield "moo"

    async def say(who: str, what: str = aiodine.depends(moo)) -> str:  # type: ignore
        return f"{who} says {what}"

    with pytest.raises(ValueError) as ctx:
        await aiodine.call_resolved(say, "cow")

    error = str(ctx.value)
    assert error == (
        "Expected coroutine or async context manager, got <class 'async_generator'>"
    )

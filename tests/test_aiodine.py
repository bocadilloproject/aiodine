import typing

import pytest
import sniffio
from anyio import sleep

import aiodine
from aiodine.compat import asynccontextmanager


async def io() -> None:
    """Simulate some kind of I/O call."""
    await sleep(1e-4)


async def get_hello() -> str:
    await io()
    return "Hello"


async def get_world() -> str:
    await io()
    return "world"


async def get_message(
    hello: str = aiodine.depends(get_hello), world: str = aiodine.depends(get_world)
) -> str:
    await io()
    return f"{hello}, {world}"


async def say(message: str = aiodine.depends(get_message), times: int = 1) -> str:
    await io()
    return message * times


@pytest.mark.anyio
async def test_vanilla_usage() -> None:
    assert await get_hello() == "Hello"
    assert await get_world() == "world"
    assert await get_message("Hola", "mundo") == "Hola, mundo"


@pytest.mark.anyio
async def test_provide_parameter() -> None:
    assert await aiodine.call_resolved(say) == "Hello, world"


@pytest.mark.anyio
async def test_callee_uses_keyword_argument() -> None:
    assert await aiodine.call_resolved(say, times=2) == "Hello, worldHello, world"


@pytest.mark.anyio
async def test_callee_overrides_provided_positional_parameter() -> None:
    assert await aiodine.call_resolved(say, "Hi") == "Hi"


@pytest.mark.anyio
async def test_callee_overrides_provided_keyword_parameter() -> None:
    assert await aiodine.call_resolved(get_message, world="mundo") == "Hello, mundo"


def test_dependable_repr() -> None:
    dependable = aiodine.depends(...)  # type: ignore
    assert repr(dependable) == "Dependable(func=Ellipsis)"


@pytest.mark.anyio
async def test_context_manager_dependable() -> None:
    cleaned_up = False

    @asynccontextmanager
    async def get_connection() -> typing.AsyncIterator[str]:
        nonlocal cleaned_up
        await io()
        yield "conn"
        cleaned_up = True

    async def view(slug: str, conn: str = aiodine.depends(get_connection)) -> tuple:
        await io()
        return (slug, conn)

    assert await aiodine.call_resolved(view, "test") == ("test", "conn")
    assert cleaned_up


@pytest.mark.anyio
async def test_class_style_context_manager_dependable() -> None:
    cleaned_up = False

    class GetConnection:
        async def __aenter__(self) -> str:
            await io()
            return "conn"

        async def __aexit__(self, *args: typing.Any) -> None:
            nonlocal cleaned_up
            await io()
            cleaned_up = True

    async def view(slug: str, conn: str = aiodine.depends(GetConnection)) -> tuple:
        await io()
        return (slug, conn)

    assert await aiodine.call_resolved(view, "test") == ("test", "conn")
    assert cleaned_up


@pytest.mark.anyio
async def call_async_context_manager() -> None:
    cleaned_up = False

    @asynccontextmanager
    async def value() -> typing.AsyncIterator[int]:
        nonlocal cleaned_up
        await io()
        yield 42
        await io()
        cleaned_up = True

    assert await aiodine.call_resolved(value) == 42
    assert cleaned_up


@pytest.mark.anyio
async def test_plain_generator_dependable_not_supported() -> None:
    async def get_value() -> typing.AsyncIterator[str]:
        yield "nope"

    async def main(value: str = aiodine.depends(get_value)) -> None:  # type: ignore
        pass

    with pytest.raises(ValueError) as ctx:
        await aiodine.call_resolved(main)

    error = str(ctx.value)
    assert error == (
        "Expected coroutine or async context manager, got <class 'async_generator'>"
    )


@pytest.mark.anyio
async def test_context_manager_dependable_cleanup_on_error() -> None:
    if sniffio.current_async_library() == "curio":
        pytest.xfail(
            "finally' clause with 'await' does not seem to "
            "run correctly on curio (cleaed_up stays False)"
        )

    cleaned_up = False

    @asynccontextmanager
    async def get_connection() -> typing.AsyncIterator[str]:
        nonlocal cleaned_up
        await io()
        try:
            yield "conn"
        finally:
            await io()
            cleaned_up = True

    async def view(conn: str = aiodine.depends(get_connection)) -> tuple:
        raise RuntimeError

    with pytest.raises(RuntimeError):
        await aiodine.call_resolved(view)

    assert cleaned_up


@pytest.mark.anyio
async def test_context_manager_dependable_no_cleanup_if_no_finally() -> None:
    cleaned_up = False

    @asynccontextmanager
    async def get_connection() -> typing.AsyncIterator[str]:
        nonlocal cleaned_up
        await io()
        yield "conn"
        await io()
        cleaned_up = True

    async def view(conn: str = aiodine.depends(get_connection)) -> tuple:
        raise RuntimeError

    with pytest.raises(RuntimeError):
        await aiodine.call_resolved(view)

    assert not cleaned_up


@pytest.mark.anyio
async def test_sub_dependencies() -> None:
    async def moo() -> str:
        await io()
        return "moo"

    async def cowsay(message: str = aiodine.depends(moo)) -> str:
        return f"Cow says: {message}"

    assert await aiodine.call_resolved(cowsay) == "Cow says: moo"


@pytest.mark.anyio
async def test_context_manager_function_sub_dependency() -> None:
    cleaned_up = False

    async def moo() -> str:
        await io()
        return "moo"

    @asynccontextmanager
    async def cowsay(message: str = aiodine.depends(moo)) -> typing.AsyncIterator[str]:
        nonlocal cleaned_up
        await io()
        yield f"Cow says: {message}"
        await io()
        cleaned_up = True

    assert await aiodine.call_resolved(cowsay) == "Cow says: moo"
    assert cleaned_up


@pytest.mark.anyio
async def test_function_context_manager_sub_dependency() -> None:
    cleaned_up = False

    @asynccontextmanager
    async def moo() -> typing.AsyncIterator[str]:
        nonlocal cleaned_up
        await io()
        yield "moo"
        await io()
        cleaned_up = True

    async def cowsay(message: str = aiodine.depends(moo)) -> str:
        return f"Cow says: {message}"

    assert await aiodine.call_resolved(cowsay) == "Cow says: moo"
    assert cleaned_up

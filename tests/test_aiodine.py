import contextlib
import typing

import pytest
from anyio import sleep

import aiodine


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


@pytest.mark.anyio
async def test_sub_dependencies() -> None:
    async def moo() -> str:
        await io()
        return "moo"

    async def cowsay(message: str = aiodine.depends(moo)) -> str:
        return f"Cow says: {message}"

    assert await aiodine.call_resolved(cowsay) == "Cow says: moo"


def test_dependable_repr() -> None:
    dependable = aiodine.depends(...)  # type: ignore
    assert repr(dependable) == "Dependable(func=Ellipsis)"


@pytest.mark.anyio
async def test_context_manager_dependable() -> None:
    steps = []

    @contextlib.asynccontextmanager
    async def get_connection() -> typing.AsyncGenerator[str, None]:
        await io()
        steps.append(1)
        yield "conn"
        steps.append(3)

    async def view(slug: str, conn: str = aiodine.depends(get_connection)) -> tuple:
        await io()
        steps.append(2)
        return (slug, conn)

    assert await aiodine.call_resolved(view, "test") == ("test", "conn")
    assert steps == [1, 2, 3]


@pytest.mark.anyio
async def test_class_style_context_manager_dependable() -> None:
    steps: typing.List[int] = []

    class GetConnection:
        async def __aenter__(self) -> str:
            steps.append(1)
            return "conn"

        async def __aexit__(self, *args: typing.Any) -> None:
            steps.append(3)

    async def view(slug: str, conn: str = aiodine.depends(GetConnection)) -> tuple:
        await io()
        steps.append(2)
        return (slug, conn)

    assert await aiodine.call_resolved(view, "test") == ("test", "conn")
    assert steps == [1, 2, 3]


@pytest.mark.anyio
async def test_plain_generator_dependable_not_supported() -> None:
    async def get_value() -> typing.AsyncGenerator[str, None]:
        yield "nope"

    async def main(value: str = aiodine.depends(get_value)) -> None:  # type: ignore
        pass

    with pytest.raises(ValueError) as ctx:
        await aiodine.call_resolved(main)

    error = str(ctx.value)
    assert error == (
        "Expected coroutine or async context manager, got <class 'async_generator'>"
    )

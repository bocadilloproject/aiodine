import asyncio
import typing

import pytest

import aiodine


async def io() -> None:
    """Simulate some kind of I/O call."""
    await asyncio.sleep(1e-4)


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


@pytest.mark.asyncio
async def test_vanilla_usage() -> None:
    assert await get_hello() == "Hello"
    assert await get_world() == "world"
    assert await get_message("Hola", "mundo") == "Hola, mundo"


@pytest.mark.asyncio
async def test_provide_parameter() -> None:
    assert await aiodine.call_resolved(say) == "Hello, world"


@pytest.mark.asyncio
async def test_callee_uses_keyword_argument() -> None:
    assert await aiodine.call_resolved(say, times=2) == "Hello, worldHello, world"


@pytest.mark.asyncio
async def test_callee_overrides_provided_positional_parameter() -> None:
    assert await aiodine.call_resolved(say, "Hi") == "Hi"


@pytest.mark.asyncio
async def test_callee_overrides_provided_keyword_parameter() -> None:
    assert await aiodine.call_resolved(get_message, world="mundo") == "Hello, mundo"


@pytest.mark.asyncio
async def test_sub_dependencies() -> None:
    async def moo() -> str:
        await io()
        return "moo"

    async def cowsay(message: str = aiodine.depends(moo)) -> str:
        return f"Cow says: {message}"

    assert await aiodine.call_resolved(cowsay) == "Cow says: moo"


def test_dependable_repr() -> None:
    dependable = aiodine.depends(...)  # type: ignore
    assert repr(dependable) == "Dependable(func=Ellipsis)"  # type: ignore

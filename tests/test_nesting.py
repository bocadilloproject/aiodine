import typing

import anyio
import pytest

import aiodine
from aiodine.compat import asynccontextmanager

from .utils import io


@pytest.mark.anyio
async def test_depend_on_function_that_depends_on_function() -> None:
    async def moo() -> str:
        await io()
        return "moo"

    async def cowsay(message: str = aiodine.depends(moo)) -> str:
        await io()
        return f"Cow says: {message}"

    async def main(cowsay: str = aiodine.depends(cowsay)) -> str:
        await io()
        return cowsay

    assert await aiodine.call_resolved(main) == "Cow says: moo"


@pytest.mark.anyio
async def test_depend_on_contextmanager_that_depends_on_function() -> None:
    event = anyio.create_event()

    async def moo() -> str:
        await io()
        return "moo"

    @asynccontextmanager
    async def cowsay(message: str = aiodine.depends(moo)) -> typing.AsyncIterator[str]:
        await io()
        yield f"Cow says: {message}"
        await event.set()

    async def main(cowsay: str = aiodine.depends(cowsay)) -> str:
        await io()
        return cowsay

    assert await aiodine.call_resolved(main) == "Cow says: moo"
    assert event.is_set()


@pytest.mark.anyio
async def test_depend_on_function_that_depends_on_contextmanager() -> None:
    event = anyio.create_event()

    @asynccontextmanager
    async def moo() -> typing.AsyncIterator[str]:
        await io()
        yield "moo"
        await event.set()

    async def cowsay(message: str = aiodine.depends(moo)) -> str:
        await io()
        return f"Cow says: {message}"

    async def main(cowsay: str = aiodine.depends(cowsay)) -> str:
        await io()
        return cowsay

    assert await aiodine.call_resolved(main) == "Cow says: moo"
    assert event.is_set()

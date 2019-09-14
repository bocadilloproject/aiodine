import typing

import pytest
import sniffio
from anyio import sleep

import aiodine
from aiodine.compat import asynccontextmanager

from .utils import io


async def get_message() -> str:
    await io()
    return "Hello, world"


async def say(message: str = aiodine.depends(get_message), times: int = 1) -> str:
    await io()
    return message * times


@pytest.mark.anyio
async def test_vanilla_usage() -> None:
    assert await get_message() == "Hello, world"
    assert await say("Hola, mundo") == "Hola, mundo"
    assert await say("Hi", times=2) == "HiHi"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "args, kwargs, output",
    [
        ((), {}, "Hello, world"),
        ((), {"times": 2}, "Hello, worldHello, world"),
        (("Hi",), {}, "Hi"),
    ],
)
async def test_depend_on_function(args: tuple, kwargs: dict, output: str) -> None:
    assert await aiodine.call_resolved(say, *args, **kwargs) == output

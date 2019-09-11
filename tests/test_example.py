import asyncio
import typing

import pytest

from aiodine import call_resolved, depends


class Result(typing.NamedTuple):
    message: str


async def make_api_call() -> Result:
    await asyncio.sleep(0.1)  # Simulate an HTTP request…
    return Result(message="Hello, world!")


async def main(data: Result = depends(make_api_call)) -> None:
    print("Fetched:", data)


def test_example(capsys: typing.Any) -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(call_resolved(main))
    captured = capsys.readouterr()
    assert captured.out.strip() == "Fetched: Result(message='Hello, world!')"

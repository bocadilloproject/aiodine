import typing
import re

import pytest

import aiodine


async def cowsay() -> None:
    pass


class CowSay:
    async def __call__(self) -> None:
        return

    def __repr__(self) -> str:
        return "Cow says moo!"


@pytest.mark.parametrize(
    "func, output",
    [
        (cowsay, f"Dependable(func={cowsay!r})"),
        (CowSay(), "Dependable(func=Cow says moo!)"),
    ],
)
def test_dependable_repr(func: typing.Callable, output: str) -> None:
    dependable = aiodine.depends(func)
    assert repr(dependable) == output

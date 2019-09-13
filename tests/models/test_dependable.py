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
@pytest.mark.parametrize("cached", (None, False, True))
def test_dependable_repr(func: typing.Callable, cached: bool, output: str) -> None:
    kwargs = {"cached": cached} if cached is not None else {}
    dependable = aiodine.depends(func, **kwargs)
    if cached:
        output = f"{output.rstrip(')')}, cached)"
    assert repr(dependable) == output


def test_dependable_equal() -> None:
    dependable = aiodine.depends(cowsay)
    assert dependable == dependable
    assert dependable == aiodine.depends(cowsay)
    assert dependable != "not a Dependable"

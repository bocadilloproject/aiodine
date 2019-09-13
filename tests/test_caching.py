import typing

import anyio
import pytest

import aiodine
from aiodine.compat import asynccontextmanager


@pytest.mark.anyio
@pytest.mark.parametrize("cached", (False, True))
@pytest.mark.parametrize("forced_cached", (None, False, True))
@pytest.mark.parametrize("use_context_manager", (False, True))
async def test_cache_function(
    cached: bool, forced_cached: typing.Optional[bool], use_context_manager: bool
) -> None:
    aiodine.CACHE.clear()
    count = 0

    moo: aiodine.models.DependableFunc[str]

    if use_context_manager:

        @asynccontextmanager
        async def moo() -> typing.AsyncIterator[str]:
            nonlocal count
            count += 1
            yield "moo"

    else:

        async def moo() -> str:
            nonlocal count
            count += 1
            return "moo"

    if cached:
        moo = aiodine.cached(moo)

    kwargs = {"cached": forced_cached} if forced_cached is not None else {}

    async def cowsay(moo: str = aiodine.depends(moo, **kwargs)) -> str:
        return f"Cow says {moo}"

    assert await aiodine.call_resolved(cowsay) == "Cow says moo"
    assert count == 1

    assert await aiodine.call_resolved(cowsay) == "Cow says moo"

    if (cached or forced_cached) and forced_cached is not False:
        assert count == 1
        assert list(aiodine.CACHE) == [aiodine.depends(moo, **kwargs)]
    else:
        assert count == 2
        assert list(aiodine.CACHE) == []

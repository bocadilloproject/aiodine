import pytest

import aiodine
from aiodine.models import DependablesCache


@pytest.mark.anyio
async def test_dependables_cache() -> None:
    cache = DependablesCache()

    @cache.cached
    async def moo() -> str:
        return "moo"

    moo_dependable = aiodine.dependencies.Dependable(moo)

    assert len(cache) == 0
    assert moo_dependable not in cache
    with pytest.raises(KeyError):
        cache[moo_dependable]

    cache[moo_dependable] = await moo()

    assert len(cache) == 1
    assert moo_dependable in cache
    assert moo not in cache
    assert list(cache) == [moo_dependable]
    assert cache[moo_dependable] == "moo"

    cache.clear()
    assert len(cache) == 0
    assert moo_dependable not in cache

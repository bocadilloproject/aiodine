import pytest
from aiodine import Store

pytestmark = pytest.mark.asyncio


async def test_from_string(store: Store):
    called = False

    @store.provider
    async def setup_stuff():
        nonlocal called
        called = True

    @store.consumer
    @store.useprovider("setup_stuff")
    async def consume():
        pass

    assert not called
    await consume()
    assert called


async def test_from_provider(store: Store):
    called = False

    @store.provider
    async def setup_stuff():
        nonlocal called
        called = True

    @store.consumer
    @store.useprovider(setup_stuff)
    async def consume():
        pass

    assert not called
    await consume()
    assert called

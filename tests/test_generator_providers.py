import pytest

from aiodine import Store

pytestmark = pytest.mark.asyncio


async def test_sync_session_yield_provider(store: Store):
    setup = False
    teardown = False

    @store.provider
    def resource():
        nonlocal setup, teardown
        setup = True
        yield "resource"
        teardown = True

    @store.resolve
    def consumer(resource: str):
        return resource.upper()

    assert await consumer() == "RESOURCE"
    assert setup
    assert teardown


async def test_async_session_yield_provider(store: Store):
    setup = False
    teardown = False

    @store.provider
    async def resource():
        nonlocal setup, teardown
        setup = True
        yield "resource"
        teardown = True

    @store.resolve
    def consumer(resource: str):
        return resource.upper()

    assert await consumer() == "RESOURCE"
    assert setup
    assert teardown

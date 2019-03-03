import pytest

from aiodine import Store

pytestmark = pytest.mark.asyncio


async def test_sync_function_yield_provider(store: Store):
    setup = False
    teardown = False

    @store.provider
    def resource():
        nonlocal setup, teardown
        setup = True
        yield "resource"
        teardown = True

    @store.consumer
    def consume(resource: str):
        return resource.upper()

    assert await consume() == "RESOURCE"
    assert setup
    assert teardown


async def test_async_function_generator_provider(store: Store):
    setup = False
    teardown = False

    @store.provider
    async def resource():
        nonlocal setup, teardown
        setup = True
        yield "resource"
        teardown = True

    @store.consumer
    def consume(resource: str):
        return resource.upper()

    assert await consume() == "RESOURCE"
    assert setup
    assert teardown


async def test_session_generator_provider(store: Store):
    setup = False
    teardown = False

    @store.provider(scope="session")
    async def resource():
        nonlocal setup, teardown
        setup = True
        yield "resource"
        teardown = True

    @store.consumer
    def consume(resource: str):
        return resource.upper()

    assert await consume() == "RESOURCE"
    assert setup
    assert not teardown

    await store.exit_session()
    assert teardown


async def test_cleanup_even_if_exception_occurred(store: Store):
    teardown = False

    @store.provider
    async def resource():
        nonlocal teardown
        yield "resource"
        teardown = True

    @store.consumer
    async def consume(resource):
        raise ValueError

    with pytest.raises(ValueError):
        await consume()

    assert teardown

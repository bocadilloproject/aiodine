import pytest
from aiodine import Store
from aiodine.exceptions import ProviderDoesNotExist

pytestmark = pytest.mark.asyncio


def declare_provider(store: Store):
    @store.provider
    async def setup():
        setup.called = True

    setup.called = False
    return setup


@pytest.mark.parametrize("lazy", (True, False))
async def test_from_string(store: Store, lazy: bool):
    if not lazy:
        setup = declare_provider(store)

    @store.consumer
    @store.useprovider("setup")
    async def consume():
        pass

    if lazy:
        setup = declare_provider(store)

    assert not setup.called
    await consume()
    assert setup.called


async def test_from_provider(store: Store):
    setup = declare_provider(store)

    @store.consumer
    @store.useprovider(setup)
    async def consume():
        pass

    assert not setup.called
    await consume()
    assert setup.called


async def test_use_unknown_provider(store: Store):
    @store.consumer
    @store.useprovider("foo")
    async def consume():
        pass

    with pytest.raises(ProviderDoesNotExist):
        await consume()

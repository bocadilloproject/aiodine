import pytest
from aiodine import Store

pytestmark = pytest.mark.asyncio


async def test_autouse_provider_is_injected_without_declaring_it(store: Store):
    used = False

    @store.provider(autouse=True)
    async def setup_stuff():
        nonlocal used
        used = True

    @store.consumer
    async def not_using_setup_stuff():
        pass

    await not_using_setup_stuff()
    assert used

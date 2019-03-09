from asyncio import sleep, gather

import pytest
from aiodine import Store

# pylint: disable=no-value-for-parameter

pytestmark = pytest.mark.asyncio


async def test_provider_value_is_none_by_default(store: Store):
    store.create_context_provider("name")

    @store.consumer
    async def get_name(name):
        return name

    assert await get_name() is None


async def test_assign_value(store: Store):
    provider = store.create_context_provider("name")

    @store.consumer
    async def get_name(name):
        return name

    with provider.assign(name="alice"):
        assert await get_name() == "alice"

    assert await get_name() is None


async def test_multiple_providers(store: Store):
    provider = store.create_context_provider("name", "title")

    @store.consumer
    async def get_them(name, title):
        return name, title

    assert await get_them() == (None, None)

    with provider.assign(name="alice", title="Slim Fox"):
        assert await get_them() == ("alice", "Slim Fox")

    assert await get_them() == (None, None)


async def test_multi_client(store: Store):
    provider = store.create_context_provider("name")

    @store.consumer
    async def get_name(name):
        return name

    async def client1():
        with provider.assign(name="alice"):
            await sleep(0.01)
            # Would get "bob" if multiple clients were not supported.
            assert await get_name() == "alice"

    async def client2():
        await sleep(0.005)
        with provider.assign(name="bob"):
            await sleep(0.01)

    await gather(client1(), client2())

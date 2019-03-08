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

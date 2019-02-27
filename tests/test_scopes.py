import pytest

from aiodine import Store


def test_providers_are_session_scoped_by_default(store: Store):
    @store.provider
    def items():
        pass

    assert items.scope == "session"


@pytest.mark.asyncio
async def test_session_provider_is_recomputed_every_time(store: Store):
    @store.provider(scope="session")
    def items():
        return []

    @store.consumer
    def add(items, value):
        items.append(value)
        return items

    assert await add(1) == [1]
    assert await add(2) == [2]  # instead of [1, 2]


@pytest.mark.asyncio
async def test_scope_provider_is_computed_once_and_reused(store: Store):
    @store.provider(scope="app")
    def items():
        return []

    @store.consumer
    def add(items, value):
        items.append(value)
        return items

    assert await add(1) == [1]
    assert await add(2) == [1, 2]
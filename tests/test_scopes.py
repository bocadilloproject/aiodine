import pytest

from aiodine import Store, scopes
from aiodine.exceptions import UnknownScope


def test_providers_are_function_scoped_by_default(store: Store):
    @store.provider
    def items():
        pass

    assert items.scope == scopes.FUNCTION


@pytest.mark.asyncio
async def test_function_provider_is_recomputed_every_time(store: Store):
    @store.provider(scope=scopes.FUNCTION)
    def items():
        return []

    @store.consumer
    def add(items, value):
        items.append(value)
        return items

    assert await add(1) == [1]
    assert await add(2) == [2]  # instead of [1, 2]


@pytest.mark.asyncio
async def test_session_provider_is_computed_once_and_reused(store: Store):
    @store.provider(scope=scopes.SESSION)
    def items():
        return []

    @store.consumer
    def add(items, value):
        items.append(value)
        return items

    assert await add(1) == [1]
    assert await add(2) == [1, 2]


def test_mapped_scopes():
    store = Store(scopes_map={"foo": scopes.FUNCTION, "sass": scopes.SESSION})

    # foo should behave like function.
    @store.provider(scope="foo")
    def items():
        pass

    assert items.scope == scopes.FUNCTION

    # sass should behave like session.
    @store.provider(scope="sass")
    def nums():
        pass

    assert nums.scope == scopes.SESSION


def test_unknown_scope(store: Store):
    with pytest.raises(UnknownScope) as ctx:

        @store.provider(scope="blabla")
        def items():
            pass

    assert "blabla" in str(ctx.value)

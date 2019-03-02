import pytest

from aiodine import Store, scopes
from aiodine.exceptions import UnknownScope


@pytest.mark.parametrize(
    "store, expected_scope",
    [
        [Store(), scopes.FUNCTION],
        [Store(default_scope=scopes.FUNCTION), scopes.FUNCTION],
        [Store(default_scope=scopes.SESSION), scopes.SESSION],
    ],
)
def test_default_scope(store, expected_scope):
    @store.provider
    def items():
        pass

    assert items.scope == expected_scope


@pytest.mark.parametrize(
    "scope, expected_second_call",
    [(scopes.SESSION, [1, 2]), (scopes.FUNCTION, [2])],
)
@pytest.mark.asyncio
async def test_reuse_of_provided_values(
    store: Store, scope, expected_second_call
):
    @store.provider(scope=scope)
    def items():
        return []

    @store.consumer
    def add(items, value):
        items.append(value)
        return items

    assert await add(1) == [1]
    assert await add(2) == expected_second_call


@pytest.mark.parametrize(
    "aliases, scope, expected",
    [
        [
            {"foo": scopes.FUNCTION, "sass": scopes.SESSION},
            "foo",
            scopes.FUNCTION,
        ],
        [{"foo": scopes.FUNCTION}, "foo", scopes.FUNCTION],
        [{"sass": scopes.SESSION}, "sass", scopes.SESSION],
        [{"sass": scopes.SESSION}, scopes.FUNCTION, scopes.FUNCTION],
        [{"foo": scopes.FUNCTION}, scopes.SESSION, scopes.SESSION],
    ],
)
@pytest.mark.asyncio
async def test_scope_aliases(aliases, scope, expected):
    store = Store(scope_aliases=aliases)

    @store.provider(scope=scope)
    def items():
        return []

    assert items.scope == expected

    @store.consumer
    def add(items, value):
        items.append(value)
        return items

    assert await add(1) == [1]
    assert await add(2) == [1, 2] if items.scope == scopes.SESSION else [2]


def test_unknown_scope(store: Store):
    with pytest.raises(UnknownScope) as ctx:

        @store.provider(scope="blabla")
        def items():
            pass

    assert "blabla" in str(ctx.value)

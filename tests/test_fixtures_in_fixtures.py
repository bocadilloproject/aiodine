import pytest

from aiodine import Store, RecursiveFixtureError


pytestmark = pytest.mark.asyncio


async def test_fixture_uses_fixture(store: Store):
    with store.will_freeze():

        @store.fixture
        def a():
            return "a"

        @store.fixture
        def b(a):
            return a * 2

    func = store.resolve(lambda b: 2 * b)
    assert await func() == "aaaa"


async def test_fixture_uses_fixture_declared_later(store: Store):
    with store.will_freeze():

        @store.fixture
        def b(a):
            return a * 2

        @store.fixture
        def a():
            return "a"

    func = store.resolve(lambda b: 2 * b)
    assert await func() == "aaaa"


async def test_detect_recursive_fixture(store: Store):
    @store.fixture
    def b(a):
        return a * 2

    with pytest.raises(RecursiveFixtureError) as ctx:

        @store.fixture
        def a(b):
            return a * 2

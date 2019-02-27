import pytest

from aiodine import Store
from aiodine.exceptions import RecursiveProviderError


pytestmark = pytest.mark.asyncio


async def test_provider_uses_provider(store: Store):
    with store.exit_freeze():

        @store.provider
        def a():
            return "a"

        @store.provider
        def b(a):
            return a * 2

    func = store.consumer(lambda b: 2 * b)
    assert await func() == "aaaa"


async def test_provider_uses_provider_declared_later(store: Store):
    with store.exit_freeze():

        @store.provider
        def b(a):
            return a * 2

        @store.provider
        def a():
            return "a"

    func = store.consumer(lambda b: 2 * b)
    assert await func() == "aaaa"


async def test_detect_recursive_provider(store: Store):
    @store.provider
    def b(a):
        return a * 2

    with pytest.raises(RecursiveProviderError) as ctx:

        @store.provider
        def a(b):
            return a * 2

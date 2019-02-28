import pytest
from inspect import iscoroutine

from aiodine import Store, scopes
from aiodine.exceptions import ProviderDeclarationError

pytestmark = pytest.mark.asyncio


async def test_use_async_provider(store: Store):
    @store.provider
    async def pitch():
        return "C#"

    @store.consumer
    def play_sync(pitch):
        return 2 * "C#"

    @store.consumer
    async def play_async(pitch):
        return 2 * "C#"

    assert await play_sync() == "C#C#"
    assert await play_async() == "C#C#"


async def test_lazy_async_provider(store: Store):
    @store.provider(lazy=True)
    async def pitch():
        return "C#"

    @store.consumer
    async def play(pitch):
        assert iscoroutine(pitch)
        return 2 * await pitch

    assert await play() == "C#C#"


async def test_lazy_provider_must_be_function_scoped(store: Store):
    with pytest.raises(ProviderDeclarationError):

        @store.provider(lazy=True, scope=scopes.SESSION)
        async def pitch():
            pass

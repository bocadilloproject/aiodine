import pytest

from aiodine import Store

pytestmark = pytest.mark.asyncio


async def test_override_provider_before_usage(store: Store):
    @store.provider
    async def hello():
        return "hello"

    @store.provider
    async def hello():
        return "HELLO"

    @store.consumer
    async def say(hello):
        return hello

    assert await say() == "HELLO"


async def test_override_provider_after_usage(store: Store):
    @store.provider
    async def hello():
        return "hello"

    @store.consumer
    async def say(hello):
        return hello

    @store.provider
    async def hello():
        return "HELLO"

    assert await say() == "HELLO"

import pytest
from aiodine import Store

pytestmark = pytest.mark.asyncio


async def test_session_provider_instanciate_on_enter(store: Store):
    setup = False

    @store.provider(scope="session")
    async def resources():
        nonlocal setup
        setup = True
        return

    @store.consumer
    def consumer(resources: None):
        pass

    async with store.session():
        assert setup


async def test_session_provider_destroyed_on_exit(store: Store):
    @store.provider(scope="session")
    async def resources():
        return ["resource"]

    @store.consumer
    def consumer(resources: list):
        resources.append("other")
        return resources

    async with store.session():
        await consumer()
        assert await consumer() == ["resource", "other", "other"]

    # Instance was reset.
    assert await consumer() == ["resource", "other"]

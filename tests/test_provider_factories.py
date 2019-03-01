import pytest

from aiodine import Store

pytestmark = pytest.mark.asyncio


async def test_provider_factory_pattern(store: Store):
    @store.provider
    async def note():
        async def _get_note(pk: int):
            return {"id": pk}

        return _get_note

    @store.consumer
    async def get_note(pk: int, note):
        return await note(pk)

    assert await get_note(10) == {"id": 10}

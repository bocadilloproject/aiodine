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


async def test_generator_provider_factory(store: Store):
    setup = False
    cleanup = False

    @store.provider
    async def note():
        nonlocal setup, cleanup
        setup = True

        async def _get_note(pk: int):
            return {"id": pk}

        yield _get_note
        cleanup = True

    @store.consumer
    async def get_note(pk: int, note):
        return await note(pk)

    assert await get_note(10) == {"id": 10}
    assert setup
    assert cleanup

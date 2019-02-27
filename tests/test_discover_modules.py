import sys

import pytest
from aiodine import Store


@pytest.fixture
def notes_module(store: Store):
    class NotesModule:
        @store.provider
        def pitch():  # pylint: disable=no-method-argument
            return "C#"

    sys.modules["notes"] = NotesModule


@pytest.mark.asyncio
@pytest.mark.usefixtures("notes_module")
async def test_discover_providers(store: Store):
    store.discover("notes")
    assert store
    assert store.has_provider("pitch")
    assert await store.consumer(lambda pitch: 2 * pitch)() == "C#C#"


def test_if_module_does_not_exist_then_error(store: Store):
    with pytest.raises(ImportError):
        store.discover("doesnotexist")

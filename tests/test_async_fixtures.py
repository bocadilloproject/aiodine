import pytest
from inspect import iscoroutine

from bocadillo.fixtures import Store, FixtureDeclarationError

pytestmark = pytest.mark.asyncio


async def test_use_async_fixture(store: Store):
    @store.fixture
    async def pitch():
        return "C#"

    @store.resolve
    def play_sync(pitch):
        return 2 * "C#"

    @store.resolve
    async def play_async(pitch):
        return 2 * "C#"

    assert await play_sync() == "C#C#"
    assert await play_async() == "C#C#"


async def test_lazy_async_fixture(store: Store):
    @store.fixture(lazy=True)
    async def pitch():
        return "C#"

    @store.resolve
    async def play(pitch):
        assert iscoroutine(pitch)
        return 2 * await pitch

    assert await play() == "C#C#"


async def test_lazy_fixture_must_be_session_scoped(store: Store):
    with pytest.raises(FixtureDeclarationError):

        @store.fixture(lazy=True, scope="other")
        async def pitch():
            pass

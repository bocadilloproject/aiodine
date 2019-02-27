import inspect

import pytest

from bocadillo.fixtures import Store, FixtureDeclarationError

pytestmark = pytest.mark.asyncio


async def test_resolve_for_func_returns_coroutine_function(store: Store):
    func = store.resolve(lambda: "test")
    assert inspect.iscoroutinefunction(func)


async def test_if_no_fixture_declared_then_behaves_like_func(store: Store):
    func = store.resolve(lambda: "test")
    assert await func() == "test"


async def test_if_fixture_does_not_exist_then_missing_argument(store: Store):
    @store.fixture
    def gra():
        return "gra"

    # "gra" exists, but not "arg"
    func = store.resolve(lambda arg: 2 * arg)

    with pytest.raises(TypeError):
        await func()

    assert await func(10) == 20


async def test_if_fixture_exists_then_injected(store: Store):
    @store.fixture
    def arg():
        return "foo"

    @store.resolve
    def func(arg):
        return 2 * arg

    assert await func() == "foofoo"


async def test_non_fixture_parameters_after_fixture_parameters_ok(store: Store):
    @store.fixture
    def pitch():
        return "C#"

    @store.resolve
    def play(pitch, duration):
        assert pitch == "C#"
        return (pitch, duration)

    assert await play(1) == ("C#", 1)
    assert await play(duration=1) == ("C#", 1)


async def test_fixture_parameters_before_fixture_parameters_fails(store: Store):
    @store.fixture
    def pitch():
        return "C#"

    with pytest.raises(FixtureDeclarationError):

        @store.resolve
        def play(duration, pitch):  # duration is before a fixture param
            pass


async def test_resolve_async_function(store: Store):
    @store.fixture
    def pitch():
        return "C#"

    @store.resolve
    async def play(pitch):
        return 2 * pitch

    assert await play() == "C#C#"

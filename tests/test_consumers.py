import inspect

import pytest
from aiodine import Store

pytestmark = pytest.mark.asyncio


async def test_consumer_returns_coroutine_function(store: Store):
    func = store.consumer(lambda: "test")
    assert inspect.iscoroutinefunction(func)


async def test_if_no_provider_decalred_then_behaves_like_func(store: Store):
    func = store.consumer(lambda: "test")
    assert await func() == "test"


async def test_if_provider_does_not_exist_then_missing_argument(store: Store):
    @store.provider
    def gra():
        return "gra"

    # "gra" exists, but not "arg"
    func = store.consumer(lambda arg: 2 * arg)

    with pytest.raises(TypeError):
        await func()

    assert await func(10) == 20


async def test_if_provider_exists_then_injected(store: Store):
    @store.provider
    def arg():
        return "foo"

    @store.consumer
    def func(arg):
        return 2 * arg

    assert await func() == "foofoo"


async def test_non_provider_parameters_after_provider_parameters_ok(
    store: Store
):
    @store.provider
    def pitch():
        return "C#"

    @store.consumer
    def play(pitch, duration):
        assert pitch == "C#"
        return (pitch, duration)

    assert await play(1) == ("C#", 1)
    assert await play(duration=1) == ("C#", 1)


async def test_non_provider_parameters_before_provider_parameters_ok(
    store: Store
):
    @store.provider
    def pitch():
        return "C#"

    @store.consumer
    def play(duration, pitch):
        assert pitch == "C#"
        return (pitch, duration)

    assert await play(1) == ("C#", 1)
    assert await play(duration=1) == ("C#", 1)


async def test_async_consumer(store: Store):
    @store.provider
    def pitch():
        return "C#"

    @store.consumer
    async def play(pitch):
        return 2 * pitch

    assert await play() == "C#C#"

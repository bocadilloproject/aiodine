import sys

import pytest

from aiodine import Store


@pytest.fixture
def providers_module(store: Store):
    class FixtureConf:
        __spec__ = "spam"  # module-like

        @store.provider
        def example():  # pylint: disable=no-method-argument
            return "foo"

    sys.modules[store.providers_module] = FixtureConf


def test_default_providers_module(store: Store):
    assert store.providers_module == "providerconf"


def test_if_no_provider_module_then_ok(store: Store):
    store.discover_default()
    assert store.empty()


@pytest.mark.asyncio
@pytest.mark.usefixtures("providers_module")
async def test_if_provider_module_then_providers_are_loaded(store: Store):
    store.discover_default()
    assert not store.empty()
    assert store.has_provider("example")
    assert await store.consumer(lambda example: 2 * example)() == "foofoo"

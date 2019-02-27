import sys

import pytest

from aiodine import Store


@pytest.fixture
def default_module(store: Store):
    class FixtureConf:
        @store.provider
        def example():  # pylint: disable=no-method-argument
            return "foo"

    sys.modules["providerconf"] = FixtureConf


def test_if_no_provider_conf_then_ok(store: Store):
    store.discover_default()
    assert not store


@pytest.mark.asyncio
@pytest.mark.usefixtures("default_module")
async def test_if_providerconf_then_providers_are_loaded(store: Store):
    store.discover_default()
    assert store
    assert "example" in store
    assert await store.resolve(lambda example: 2 * example)() == "foofoo"

import sys

import pytest

from aiodine import Store


@pytest.fixture
def fixtureconf(store: Store):
    class FixtureConf:
        # Simulates a `fixtureconf` module.
        @store.fixture
        def example():  # pylint: disable=no-method-argument
            return "foo"

    sys.modules["fixtureconf"] = FixtureConf


def test_if_no_fixture_conf_then_ok(store: Store):
    store.discover_default()
    assert not store


@pytest.mark.asyncio
@pytest.mark.usefixtures("fixtureconf")
async def test_if_fixtureconf_then_fixtures_are_loaded(store: Store):
    store.discover_default()
    assert store
    assert "example" in store
    assert await store.resolve(lambda example: 2 * example)() == "foofoo"

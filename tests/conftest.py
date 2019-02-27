import pytest

from bocadillo.fixtures import Store


@pytest.fixture(name="store")
def fixture_store() -> Store:
    return Store()

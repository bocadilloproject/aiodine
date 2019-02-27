import pytest

from aiodine import Store


@pytest.fixture
def store() -> Store:
    return Store()

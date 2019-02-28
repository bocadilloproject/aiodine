from importlib import reload

import pytest

import aiodine
from aiodine import Store


@pytest.fixture(params=[Store, lambda: reload(aiodine)])
def store(request) -> Store:
    cls = request.param
    return cls()

"""Generic providers with more complex behavior."""

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .store import Store


class ContextProvider:
    def __init__(self, store: "Store", *names: str):
        self._store = store
        self._values: Dict[str, Any] = {}

        for name in names:
            self._build_provider(name)

    def _build_provider(self, name):
        self._values[name] = None

        async def provider():
            return self._values[name]

        return self._store.provider(name=name)(provider)

    @contextmanager
    def assign(self, **kwargs):
        for key, val in kwargs.items():
            self._values[key] = val
        try:
            yield
        finally:
            for key in kwargs:
                self._values[key] = None

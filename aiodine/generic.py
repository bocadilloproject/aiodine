"""Generic providers with more complex behavior."""

from contextlib import contextmanager
from typing import TYPE_CHECKING, Dict
from contextvars import ContextVar

if TYPE_CHECKING:
    from .store import Store


class ContextProvider:
    def __init__(self, store: "Store", *names: str):
        self._store = store
        self._variables: Dict[str, ContextVar] = {}

        for name in names:
            self._build_provider(name)

    def _build_provider(self, name):
        self._variables[name] = ContextVar(name, default=None)

        async def provider():
            return self._variables[name].get()

        return self._store.provider(name=name)(provider)

    @contextmanager
    def assign(self, **kwargs):
        for key, val in kwargs.items():
            self._variables[key].set(val)
        try:
            yield
        finally:
            for key in kwargs:
                self._variables[key].set(None)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .store import Store


# NOTE: can't use @asynccontextmanager from contextlib because it was
# only added in Python 3.7.
class Session:
    def __init__(self, store: "Store"):
        self._store = store

    async def __aenter__(self):
        await self._store.enter_session()
        return None

    async def __aexit__(self, *args):
        await self._store.exit_session()

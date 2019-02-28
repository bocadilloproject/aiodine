from .providers import Provider
from .store import Store

# pylint: disable=invalid-name
_STORE = Store()

provider = _STORE.provider
consumer = _STORE.consumer
has_provider = _STORE.has_provider
providers_module = _STORE.providers_module
empty = _STORE.empty
discover = _STORE.discover
discover_default = _STORE.discover_default
freeze = _STORE.freeze
exit_freeze = _STORE.exit_freeze

__version__ = "0.1.2"

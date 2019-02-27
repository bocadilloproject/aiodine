from .providers import Provider, ProviderDeclarationError
from .store import Store

# pylint: disable=invalid-name
_STORE = Store()

provider = _STORE.provider
consumer = _STORE.consumer
discover_providers = _STORE.discover_providers
freeze = _STORE.freeze
will_freeze = _STORE.will_freeze
discover_default = _STORE.discover_default
discover_providers = _STORE.discover_providers
has_provider = _STORE.has_provider
empty = _STORE.empty

__version__ = "0.0.0"

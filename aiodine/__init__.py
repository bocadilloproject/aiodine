from .providers import Provider, ProviderDeclarationError
from .store import Store

# pylint: disable=invalid-name
_STORE = Store()
provider = _STORE.provider
consumer = _STORE.consumer
discover_providers = _STORE.discover_providers

__version__ = "0.0.0"

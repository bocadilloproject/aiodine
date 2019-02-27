from .providers import Provider, ProviderDeclarationError
from .store import Store

_STORE = Store()
provider = _STORE.provider  # pylint: disable=invalid-name
discover_providers = _STORE.discover_providers  # pylint: disable=invalid-name

__version__ = "0.0.0"

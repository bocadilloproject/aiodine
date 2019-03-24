import inspect
from contextlib import contextmanager
from functools import partial
from importlib import import_module
from importlib.util import find_spec
from typing import Callable, Dict, Optional, Union

from . import scopes
from .consumers import Consumer
from .datatypes import CoroutineFunction
from .exceptions import RecursiveProviderError, UnknownScope
from .providers import ContextProvider, Provider, SessionProvider
from .sessions import Session

DEFAULT_PROVIDER_MODULE = "providerconf"


class Store:

    __slots__ = (
        "providers",
        "autouse_providers",
        "scope_aliases",
        "default_scope",
        "providers_module",
        "session_providers",
    )

    def __init__(
        self,
        providers_module=DEFAULT_PROVIDER_MODULE,
        scope_aliases: Dict[str, str] = None,
        default_scope: str = scopes.FUNCTION,
    ):
        if scope_aliases is None:
            scope_aliases = {}

        self.providers: Dict[str, Provider] = {}
        self.session_providers: Dict[str, SessionProvider] = {}
        self.autouse_providers: Dict[str, Provider] = {}
        self.scope_aliases = scope_aliases
        self.default_scope = default_scope
        self.providers_module = providers_module

    # Inspection.

    def empty(self):
        return not self.providers

    def has_provider(self, name: str) -> bool:
        return name in self.providers

    def _get(self, name: str) -> Optional[Provider]:
        return self.providers.get(name)

    def _get_providers(self, func: Callable) -> Dict[str, Provider]:
        providers = {
            param: self._get(param)
            for param in inspect.signature(func).parameters
        }
        return dict(filter(lambda item: item[1] is not None, providers.items()))

    # Provider discovery.

    def discover_default(self):
        if find_spec(self.providers_module) is None:
            # Module does not exist.
            return
        self.discover(self.providers_module)

    @staticmethod
    def discover(*module_paths: str):
        for module_path in module_paths:
            import_module(module_path)

    # Provider registration.

    def provider(
        self,
        func: Callable = None,
        scope: str = None,
        name: str = None,
        lazy: bool = False,
        autouse: bool = False,
    ) -> Provider:
        if func is None:
            return partial(
                self.provider,
                scope=scope,
                name=name,
                lazy=lazy,
                autouse=autouse,
            )

        if scope is None:
            scope = self.default_scope
        else:
            scope = self.scope_aliases.get(scope, scope)

        if scope not in scopes.ALL:
            raise UnknownScope(scope)

        if name is None:
            name = func.__name__

        # NOTE: save the new provider before checking for recursion,
        # so that its dependants can detect it as a dependency.
        prov = Provider.create(
            func, name=name, scope=scope, lazy=lazy, autouse=autouse
        )
        self._add(prov)

        self._check_for_recursive_providers(name, func)

        return prov

    def _add(self, prov: Provider):
        self.providers[prov.name] = prov
        if isinstance(prov, SessionProvider):
            self.session_providers[prov.name] = prov
        if prov.autouse:
            self.autouse_providers[prov.name] = prov

    # Provider recursion check.

    def _check_for_recursive_providers(self, name: str, func: Callable):
        for other_name, other in self._get_providers(func).items():
            if name in self._get_providers(other.func):
                raise RecursiveProviderError(name, other_name)

    # Consumers.

    def consumer(
        self, consumer_function: Union[partial, Callable, CoroutineFunction]
    ) -> Consumer:
        return Consumer(self, consumer_function)

    # Used providers.

    def useprovider(self, *providers: Union[str, Provider]):
        def decorate(func):
            func.__useproviders__ = [
                prov if isinstance(prov, Provider) else self._get(prov)
                for prov in providers
            ]
            return func

        return decorate

    @staticmethod
    def get_used_providers(func: Callable):
        return getattr(func, "__useproviders__", [])

    # Context providers.

    def create_context_provider(self, *args, **kwargs):
        return ContextProvider(self, *args, **kwargs)

    # Provider-in-providers freezing.

    def freeze(self):
        for prov in self.providers.values():
            prov.func = self.consumer(prov.func)

    @contextmanager
    def exit_freeze(self):
        yield
        self.freeze()

    # Sessions.

    async def enter_session(self):
        for provider in self.session_providers.values():
            await provider.enter_session()

    async def exit_session(self):
        for provider in self.session_providers.values():
            await provider.exit_session()

    def session(self):
        return Session(self)

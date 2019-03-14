import inspect
from contextlib import contextmanager, suppress
from functools import partial, wraps
from importlib import import_module
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple, Union

from . import scopes
from .compat import AsyncExitStack, wrap_async
from .datatypes import CoroutineFunction
from .exceptions import (
    ConsumerDeclarationError,
    RecursiveProviderError,
    UnknownScope,
)
from .providers import Provider, SessionProvider, ContextProvider

PositionalProviders = List[Tuple[str, Provider]]
KeywordProviders = Dict[str, Provider]

# Sentinel for parameters that have no provider.
_NO_PROVIDER = object()


class ResolvedProviders(NamedTuple):

    positional: PositionalProviders
    keyword: KeywordProviders
    external: List[Provider]

    def __bool__(self):
        return (
            bool(self.positional) or bool(self.keyword) or bool(self.external)
        )


class Store:

    __slots__ = (
        "providers",
        "scope_aliases",
        "default_scope",
        "providers_module",
        "_session_providers",
        "_autouse_providers",
    )

    def __init__(
        self,
        providers_module="providerconf",
        scope_aliases: Dict[str, str] = None,
        default_scope: str = scopes.FUNCTION,
    ):
        if scope_aliases is None:
            scope_aliases = {}

        self.providers: Dict[str, Provider] = {}
        self._session_providers: Dict[str, SessionProvider] = {}
        self._autouse_providers: Dict[str, Provider] = {}
        self.scope_aliases = scope_aliases
        self.default_scope = default_scope
        self.providers_module = providers_module

    def empty(self):
        return not self.providers

    def has_provider(self, name: str) -> bool:
        return name in self.providers

    def _get(self, name: str) -> Optional[Provider]:
        return self.providers.get(name)

    def discover_default(self):
        with suppress(ImportError):
            self.discover(self.providers_module)

    def discover(self, *module_paths: str):
        for module_path in module_paths:
            import_module(module_path)

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
            self._session_providers[prov.name] = prov
        if prov.autouse:
            self._autouse_providers[prov.name] = prov

    def _check_for_recursive_providers(self, name: str, func: Callable):
        for other_name, other in self._get_providers(func).items():
            if name in self._get_providers(other.func):
                raise RecursiveProviderError(name, other_name)

    def _get_providers(self, func: Callable) -> Dict[str, Provider]:
        providers = {
            param: self._get(param)
            for param in inspect.signature(func).parameters
        }
        return dict(filter(lambda item: item[1] is not None, providers.items()))

    def _resolve_providers(self, consumer: Callable) -> ResolvedProviders:
        positional: PositionalProviders = []
        keyword: KeywordProviders = {}
        external = [
            *self._autouse_providers.values(),
            *getattr(consumer, "__useproviders__", []),
        ]

        for name, parameter in inspect.signature(consumer).parameters.items():
            prov: Optional[Provider] = self.providers.get(name)

            if prov is None:
                positional.append((name, _NO_PROVIDER))
                continue

            if parameter.kind == inspect.Parameter.KEYWORD_ONLY:
                keyword[name] = prov
            else:
                positional.append((name, prov))

        return ResolvedProviders(
            positional=positional, keyword=keyword, external=external
        )

    def consumer(
        self, consumer: Union[partial, Callable, CoroutineFunction]
    ) -> CoroutineFunction:
        if isinstance(consumer, partial):
            if not inspect.iscoroutinefunction(consumer.func):
                raise ConsumerDeclarationError(
                    "'partial' consumers must wrap an async function"
                )
        elif not inspect.iscoroutinefunction(consumer):
            consumer = wrap_async(consumer)

        assert (
            isinstance(consumer, partial)
            and inspect.iscoroutinefunction(consumer.func)
            or inspect.iscoroutinefunction(consumer)
        )

        providers = self._resolve_providers(consumer)

        if not providers:
            return consumer

        @wraps(consumer)
        async def with_providers(*args, **kwargs):
            async with AsyncExitStack() as stack:

                async def _get_value(prov: Provider):
                    if prov.lazy:
                        return prov(stack)
                    return await prov(stack)

                for prov in providers.external:
                    await _get_value(prov)

                args = list(args)
                injected_args = []
                for name, prov in providers.positional:
                    if prov is _NO_PROVIDER:
                        # No provider exists for this argument. Get it from
                        # `kwargs` in priority, and default to `args`.
                        if name in kwargs:
                            injected_args.append(kwargs.pop(name))
                            continue
                        with suppress(IndexError):
                            injected_args.append(args.pop())
                        continue
                    # A provider exists for this argument. Use it!
                    injected_args.append(await _get_value(prov))

                injected_kwargs = {
                    name: await _get_value(prov)
                    for name, prov in providers.keyword.items()
                    if name not in kwargs
                }

                return await consumer(*injected_args, **injected_kwargs)

        return with_providers

    def useprovider(self, *providers: Union[str, Provider]):
        def decorate(func):
            func.__useproviders__ = [
                prov if isinstance(prov, Provider) else self._get(prov)
                for prov in providers
            ]
            return func

        return decorate

    def create_context_provider(self, *args, **kwargs):
        return ContextProvider(self, *args, **kwargs)

    def freeze(self):
        """Resolve providers consumed by each provider."""
        for prov in self.providers.values():
            prov.func = self.consumer(prov.func)

    @contextmanager
    def exit_freeze(self):
        yield
        self.freeze()

    async def enter_session(self):
        for provider in self._session_providers.values():
            await provider.enter_session()

    async def exit_session(self):
        for provider in self._session_providers.values():
            await provider.exit_session()

    def session(self):
        return _Session(self)


# NOTE: can't use @asynccontextmanager from contextlib because it was
# only added in Python 3.7.
class _Session:
    def __init__(self, store: Store):
        self._store = store

    async def __aenter__(self):
        await self._store.enter_session()
        return None

    async def __aexit__(self, *args):
        await self._store.exit_session()

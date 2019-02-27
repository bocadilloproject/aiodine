import inspect
from contextlib import contextmanager, suppress
from functools import partial, wraps
from importlib import import_module
from typing import Any, Callable, Dict, List, Optional, Union, NamedTuple

from . import scopes
from .compat import AsyncExitStack, wrap_async
from .datatypes import CoroutineFunction
from .exceptions import ProviderDeclarationError, RecursiveProviderError
from .providers import Provider


PositionalProviders = List[Provider]
KeywordProviders = Dict[str, Provider]


class ResolvedProviders(NamedTuple):

    positional: PositionalProviders
    keyword: KeywordProviders

    def __bool__(self):
        return bool(self.positional) or bool(self.keyword)


class Store:

    __slots__ = ("providers",)

    DEFAULT_PROVIDERS_MODULE = "providerconf"

    def __init__(self):
        self.providers: Dict[str, Provider] = {}

    @property
    def empty(self):
        return not self.providers

    def _exists(self, name: str) -> bool:
        return name in self.providers

    def _get(self, name: str) -> Optional[Provider]:
        return self.providers.get(name)

    def discover_default(self):
        with suppress(ImportError):
            self.discover_providers(self.DEFAULT_PROVIDERS_MODULE)

    def discover_providers(self, *module_paths: str):
        for module_path in module_paths:
            import_module(module_path)

    def provider(
        self,
        func: Callable = None,
        scope: str = scopes.SESSION,
        name: str = None,
        lazy: bool = False,
    ) -> Provider:
        if func is None:
            return partial(self.provider, scope=scope, name=name, lazy=lazy)

        if name is None:
            name = func.__name__

        # NOTE: save the new provider before checking for recursion,
        # so that its dependants can detect it as a dependency.
        prov = Provider.create(func, name=name, scope=scope, lazy=lazy)
        self._add(prov)

        self._check_for_recursive_providers(name, func)

        return prov

    def _add(self, prov: Provider):
        self.providers[prov.name] = prov

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

        # NOTE: This flag goes down when we process a non-provider parameter.
        # It allows to detect provider parameters declared *after*
        # non-provider parameters.
        processing_providers = True

        for name, parameter in inspect.signature(consumer).parameters.items():
            prov: Optional[Provider] = self.providers.get(name)

            if prov is None:
                processing_providers = False
                continue

            if not processing_providers:
                raise ProviderDeclarationError(
                    "Provider parameters must be declared *before* other "
                    "parameters, so that they can be deterministically passed "
                    "to the consumer."
                )

            if parameter.kind == inspect.Parameter.KEYWORD_ONLY:
                keyword[name] = prov
            else:
                positional.append(prov)

        return ResolvedProviders(positional=positional, keyword=keyword)

    def consumer(
        self, consumer: Union[Callable, CoroutineFunction]
    ) -> CoroutineFunction:
        if not inspect.iscoroutinefunction(consumer):
            consumer = wrap_async(consumer)

        assert inspect.iscoroutinefunction(consumer)

        providers = self._resolve_providers(consumer)

        if not providers:
            return consumer

        @wraps(consumer)
        async def with_providers(*args, **kwargs):
            # Evaluate the providers when the function is actually called.
            async with AsyncExitStack() as stack:

                async def _get_value(prov):
                    return prov(stack) if prov.lazy else await prov(stack)

                injected_args = [
                    await _get_value(prov) for prov in providers.positional
                ]
                injected_kwargs = {
                    name: await _get_value(prov)
                    for name, prov in providers.keyword.items()
                }

                # NOTE: injected args must be given first by convention.
                # The order for kwargs should not matter.
                return await consumer(
                    *injected_args, *args, **injected_kwargs, **kwargs
                )

        return with_providers

    def freeze(self):
        """Resolve providers consumed by each provider."""
        for prov in self.providers.values():
            prov.func = self.consumer(prov.func)

    @contextmanager
    def will_freeze(self):
        yield
        self.freeze()

    def __contains__(self, element: Any) -> bool:
        return self._exists(element)

    def __bool__(self) -> bool:
        return not self.empty

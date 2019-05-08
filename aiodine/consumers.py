import inspect
import sys
from contextlib import suppress
from functools import WRAPPER_ASSIGNMENTS, partial, update_wrapper
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Union,
)

from .compat import AsyncExitStack, wrap_async
from .datatypes import CoroutineFunction
from .exceptions import ConsumerDeclarationError

if TYPE_CHECKING:  # pragma: no cover
    from .store import Store
    from .providers import Provider

PositionalProviders = List[Tuple[str, "Provider"]]
KeywordProviders = Dict[str, "Provider"]

# Sentinel for parameters that have no provider.
_NO_PROVIDER = object()


class ResolvedProviders(NamedTuple):

    positional: PositionalProviders
    keyword: KeywordProviders
    external: List["Provider"]


WRAPPER_IGNORE = {"__module__"}
if sys.version_info < (3, 7):  # pragma: no cover
    WRAPPER_IGNORE.add("__qualname__")

WRAPPER_ASSIGNMENTS = set(WRAPPER_ASSIGNMENTS) - WRAPPER_IGNORE
WRAPPER_SLOTS = {"__wrapped__", *WRAPPER_ASSIGNMENTS}


class Consumer:

    __slots__ = ("store", "func", "signature", *WRAPPER_SLOTS)

    def __init__(
        self,
        store: "Store",
        consumer_function: Union[partial, Callable, CoroutineFunction],
    ):
        self.store = store

        if isinstance(consumer_function, partial):
            if not inspect.iscoroutinefunction(consumer_function.func):
                raise ConsumerDeclarationError(
                    "'partial' consumer functions must wrap an async function"
                )
        else:
            if not inspect.isfunction(
                consumer_function
            ) and not inspect.ismethod(consumer_function):
                assert callable(consumer_function), "consumers must be callable"
                consumer_function = consumer_function.__call__

            if not inspect.iscoroutinefunction(consumer_function):
                consumer_function = wrap_async(consumer_function)

        self.func = consumer_function
        update_wrapper(
            self, self.func, assigned=WRAPPER_ASSIGNMENTS, updated=()
        )

    def resolve(self) -> ResolvedProviders:
        positional: PositionalProviders = []
        keyword: KeywordProviders = {}
        external = [
            *self.store.autouse_providers.values(),
            *self.store.get_used_providers(self.func),
        ]

        for name, parameter in inspect.signature(self.func).parameters.items():
            prov: Optional["Provider"] = self.store.providers.get(
                name, _NO_PROVIDER
            )

            if parameter.kind == inspect.Parameter.KEYWORD_ONLY:
                keyword[name] = prov
            else:
                positional.append((name, prov))

        return ResolvedProviders(
            positional=positional, keyword=keyword, external=external
        )

    async def __call__(self, *args, **kwargs):
        # TODO: cache providers after first call for better performance.
        providers = self.resolve()

        async with AsyncExitStack() as stack:

            async def _get_value(prov: "Provider"):
                if prov.lazy:
                    return prov(stack)
                return await prov(stack)

            for prov in providers.external:
                await _get_value(prov)

            # Create a stack out of the positional arguments.
            # Reverse it so we can `.pop()` out of it while
            # keeping the final order of arguments.
            args = list(reversed(args))

            injected_args = []
            for name, prov in providers.positional:
                if name in kwargs:
                    # Use values from keyword arguments in priority.
                    injected_args.append(kwargs.pop(name))
                    continue
                elif prov is _NO_PROVIDER:
                    # No provider exists. Use the next positional argument.
                    with suppress(IndexError):
                        injected_args.append(args.pop())
                else:
                    # A provider exists for this argument. Use it!
                    injected_args.append(await _get_value(prov))

            injected_kwargs = {}
            for name, prov in providers.keyword.items():
                if name in kwargs or prov is _NO_PROVIDER:
                    with suppress(KeyError):
                        injected_kwargs[name] = kwargs.pop(name)
                else:
                    injected_kwargs[name] = await _get_value(prov)

            return await self.func(*injected_args, **injected_kwargs)

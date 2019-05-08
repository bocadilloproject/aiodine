import inspect
from contextlib import contextmanager, suppress
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Union,
)

from . import scopes
from .compat import (
    AsyncExitStack,
    wrap_async,
    wrap_generator_async,
    ContextVar,
    Token,
)
from .datatypes import CoroutineFunction
from .exceptions import ProviderDeclarationError

if TYPE_CHECKING:  # pragma: no cover
    from .store import Store


async def _terminate_agen(async_gen: AsyncGenerator):
    with suppress(StopAsyncIteration):
        await async_gen.asend(None)


class Provider:
    """Base class for providers.

    This is mostly a wrapper around a provider function, along with
    some metadata.
    """

    __slots__ = ("func", "name", "scope", "lazy", "autouse")

    def __init__(
        self, func: Callable, name: str, scope: str, lazy: bool, autouse: bool
    ):
        if lazy and scope != scopes.FUNCTION:
            raise ProviderDeclarationError(
                "Lazy providers must be function-scoped"
            )

        if inspect.isgeneratorfunction(func):
            func = wrap_generator_async(func)
        elif inspect.isasyncgenfunction(func):
            pass
        elif not inspect.iscoroutinefunction(func):
            func = wrap_async(func)

        assert inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(
            func
        )

        self.func: Union[AsyncGenerator, CoroutineFunction] = func
        self.name = name
        self.scope = scope
        self.lazy = lazy
        self.autouse = autouse

    @classmethod
    def create(cls, func, **kwargs) -> "Provider":
        """Factory method to build a provider of the appropriate scope."""
        scope: Optional[str] = kwargs.get("scope")
        if scope == scopes.SESSION:
            return SessionProvider(func, **kwargs)
        return FunctionProvider(func, **kwargs)

    # NOTE: the returned value is an awaitable, so we *must not*
    # declare this function as `async` — its return value should already be.
    def __call__(self, stack: AsyncExitStack) -> Awaitable:
        raise NotImplementedError


class FunctionProvider(Provider):
    """Represents a function-scoped provider.

    Its value is recomputed every time the provider is called.
    """

    def __call__(self, stack: AsyncExitStack) -> Awaitable:
        value: Union[Awaitable, AsyncGenerator] = self.func()

        if inspect.isasyncgen(value):
            agen = value
            # We cannot use `await` in here => define a coroutine function
            # and return the (awaitable) coroutine itself.

            async def get_value() -> Any:
                # Executes setup + `yield <some_value>`.
                val = await agen.asend(None)
                # Registers cleanup to be executed when the stack exits.
                stack.push_async_callback(partial(_terminate_agen, agen))
                return val

            value: Awaitable = get_value()

        return value


class SessionProvider(Provider):
    """Represents a session-scoped provider.

    When called, it builds its instance if necessary and returns it. This
    means that the underlying provider is only built once and is reused
    across function calls.
    """

    __slots__ = Provider.__slots__ + ("_instance", "_generator")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._instance: Optional[Any] = None
        self._generator: Optional[AsyncGenerator] = None

    async def enter_session(self):
        value = self.func()

        if inspect.isawaitable(value):
            value = await value

        if inspect.isasyncgen(value):
            agen = value
            value = await agen.asend(None)
            self._generator = agen

        self._instance = value

    async def exit_session(self):
        if self._generator is not None:
            await _terminate_agen(self._generator)
            self._generator = None
        self._instance = None

    async def _get_instance(self) -> Any:
        if self._instance is None:
            await self.enter_session()
        return self._instance

    def __call__(self, stack: AsyncExitStack) -> Awaitable:
        return self._get_instance()


class ContextProvider:
    """A provider of context-local values.

    This provider is implemented using the ``contextvars`` module.

    Parameters
    ----------
    store : Store
    *names : str
        The name of the variables to provide. For each variable, a
        ``ContextVar`` is created and used by a new provider named
        after the variable.
    """

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

    def _set(self, **values: Any) -> List[Token]:
        # Set new values for the given variables.
        tokens = []
        for name, val in values.items():
            token = self._variables[name].set(val)
            tokens.append(token)
        return tokens

    def _reset(self, *tokens: Token):
        # Reset variables to their previous value using the given tokens.
        for token in tokens:
            self._variables[token.var.name].reset(token)

    @contextmanager
    def assign(self, **values: Any):
        """Context manager to assign values to variables.

        Only the variables for the current context are changed. Values for
        other contexts are unaffected.

        Variables are reset to their previous value on exit.

        Parameters
        ----------
        **values : any
        """
        tokens = self._set(**values)
        try:
            yield
        finally:
            self._reset(*tokens)

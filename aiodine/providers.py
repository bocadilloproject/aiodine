from functools import update_wrapper, partial
from contextlib import suppress
from typing import Any, Awaitable, Callable, Optional, Union, AsyncGenerator
import inspect

from .datatypes import CoroutineFunction
from .compat import wrap_async, wrap_generator_async, AsyncExitStack
from .exceptions import ProviderDeclarationError

SCOPE_SESSION = "session"
SCOPE_APP = "app"


async def _terminate_agen(async_gen: AsyncGenerator):
    with suppress(StopAsyncIteration):
        await async_gen.asend(None)


class Provider:
    """Represents a provider.

    This is mostly a wrapper around a provider function, along with
    some metadata.
    """

    def __init__(self, func: Callable, name: str, scope: str, lazy: bool):
        if lazy and scope != SCOPE_SESSION:
            raise ProviderDeclarationError(
                "Lazy providers must be session-scoped"
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

        update_wrapper(self, self.func)

    @classmethod
    def create(cls, func, **kwargs) -> "Provider":
        """Factory method to build a provider of the appropriate scope."""
        scope: Optional[str] = kwargs.get("scope")
        if scope == SCOPE_APP:
            return AppProvider(func, **kwargs)
        return Provider(func, **kwargs)

    def __repr__(self) -> str:
        return (
            f"<Provider name={self.name}, scope={self.scope}, func={self.func}>"
        )

    # NOTE: the returned value is an awaitable, so we *must not*
    # declare this function as `async` — its return value already is.
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


class AppProvider(Provider):
    """Represents an app-scoped provider.

    When called, it builds its instance if necessary and returns it. This
    means that the underlying provider is only built once and is reused
    across sessions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._instance: Any = None

    async def _get_instance(self):
        if self._instance is None:
            self._instance = await self.func()
        return self._instance

    def __call__(self, stack: AsyncExitStack) -> Awaitable:
        return self._get_instance()

from functools import wraps, update_wrapper, partial
from contextlib import suppress, contextmanager
from importlib import import_module
from typing import (
    Any,
    Awaitable,
    Dict,
    List,
    Callable,
    Tuple,
    Optional,
    Union,
    AsyncGenerator,
)
import inspect

from .compat import wrap_async, wrap_generator_async, AsyncExitStack

CoroutineFunction = Callable[..., Awaitable]
SCOPE_SESSION = "session"
SCOPE_APP = "app"


class FixtureDeclarationError(Exception):
    """Base exception for situations when a fixture was ill-declared."""


class RecursiveFixtureError(FixtureDeclarationError):
    """Raised when two fixtures depend on each other."""

    def __init__(self, first: str, second: str):
        message = (
            "recursive fixture detected: "
            f"{first} and {second} depend on each other."
        )
        super().__init__(message)


async def _terminate_agen(async_gen: AsyncGenerator):
    with suppress(StopAsyncIteration):
        await async_gen.asend(None)


class Fixture:
    """Represents a fixture.

    This is mostly a wrapper around a fixture function, along with
    some metadata.
    """

    def __init__(self, func: Callable, name: str, scope: str, lazy: bool):
        if lazy and scope != SCOPE_SESSION:
            raise FixtureDeclarationError(
                "Lazy fixtures must be session-scoped"
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
    def create(cls, func, **kwargs) -> "Fixture":
        """Factory method to build a fixture of the appropriate scope."""
        scope: Optional[str] = kwargs.get("scope")
        if scope == SCOPE_APP:
            return AppFixture(func, **kwargs)
        return Fixture(func, **kwargs)

    def __repr__(self) -> str:
        return (
            f"<Fixture name={self.name}, scope={self.scope}, func={self.func}>"
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


class AppFixture(Fixture):
    """Represents an app-scoped fixture.

    When called, it builds its instance if necessary and returns it. This
    means that the underlying fixture is only built once and is reused
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


class Store:

    DEFAULT_FIXTURES_MODULE = "fixtureconf"

    def __init__(self):
        self.fixtures: Dict[str, Fixture] = {}

    @property
    def empty(self):
        return not self.fixtures

    def _exists(self, name: str) -> bool:
        return name in self.fixtures

    def _get(self, name: str) -> Optional[Fixture]:
        return self.fixtures.get(name)

    def discover_default(self):
        with suppress(ImportError):
            self.discover_fixtures(self.DEFAULT_FIXTURES_MODULE)

    def discover_fixtures(self, *module_paths: str):
        for module_path in module_paths:
            import_module(module_path)

    def fixture(
        self,
        func: Callable = None,
        scope: str = SCOPE_SESSION,
        name: str = None,
        lazy: bool = False,
    ) -> Fixture:
        if func is None:
            return partial(self.fixture, scope=scope, name=name, lazy=lazy)

        if name is None:
            name = func.__name__

        # NOTE: save the new fixture before checking for recursion,
        # so that its dependants can detect it as a dependency.
        fixt = Fixture.create(func, name=name, scope=scope, lazy=lazy)
        self._add(fixt)

        self._check_for_recursive_fixtures(name, func)

        return fixt

    def _add(self, fixt: Fixture):
        self.fixtures[fixt.name] = fixt

    def _check_for_recursive_fixtures(self, name: str, func: Callable):
        for other_name, other in self._get_fixtures(func).items():
            if name in self._get_fixtures(other.func):
                raise RecursiveFixtureError(name, other_name)

    def _get_fixtures(self, func: Callable) -> Dict[str, Fixture]:
        fixtures = {
            param: self._get(param)
            for param in inspect.signature(func).parameters
        }
        return dict(filter(lambda item: item[1] is not None, fixtures.items()))

    def _resolve_fixtures(self, func: Callable) -> Tuple[list, dict]:
        args_fixtures: List[Tuple[str, Fixture]] = []
        kwargs_fixtures: Dict[str, Fixture] = {}

        # NOTE: This flag goes down when we process a non-fixture parameter.
        # It allows to detect fixture parameters declared *after*
        # non-fixture parameters.
        processing_fixtures = True

        for name, parameter in inspect.signature(func).parameters.items():
            fixt: Optional[Fixture] = self.fixtures.get(name)

            if fixt is None:
                processing_fixtures = False
                continue

            if not processing_fixtures:
                raise FixtureDeclarationError(
                    "Fixture parameters must be declared *before* other "
                    "parameters, so that they can be deterministically passed "
                    "to the consuming function."
                )

            if parameter.kind == inspect.Parameter.KEYWORD_ONLY:
                kwargs_fixtures[name] = fixt
            else:
                args_fixtures.append((name, fixt))

        return args_fixtures, kwargs_fixtures

    def resolve(
        self, func: Union[Callable, CoroutineFunction]
    ) -> CoroutineFunction:
        if not inspect.iscoroutinefunction(func):
            func = wrap_async(func)

        assert inspect.iscoroutinefunction(func)

        args_fixtures, kwargs_fixtures = self._resolve_fixtures(func)

        if not args_fixtures and not kwargs_fixtures:
            return func

        @wraps(func)
        async def with_fixtures(*args, **kwargs):
            # Evaluate the fixtures when the function is actually called.
            async with AsyncExitStack() as stack:

                async def _instanciate(fixt):
                    return fixt(stack) if fixt.lazy else await fixt(stack)

                injected_args = [
                    await _instanciate(fixt) for _, fixt in args_fixtures
                ]
                injected_kwargs = {
                    name: await _instanciate(fixt)
                    for name, fixt in kwargs_fixtures.items()
                }

                # NOTE: injected args must be given first by convention.
                # The order for kwargs should not matter.
                return await func(
                    *injected_args, *args, **injected_kwargs, **kwargs
                )

        return with_fixtures

    def freeze(self):
        """Resolve fixtures used by each fixture."""
        for fixt in self.fixtures.values():
            fixt.func = self.resolve(fixt.func)

    @contextmanager
    def will_freeze(self):
        yield
        self.freeze()

    def __contains__(self, element: Any) -> bool:
        return self._exists(element)

    def __bool__(self) -> bool:
        return not self.empty


_STORE = Store()
fixture = _STORE.fixture  # pylint: disable=invalid-name
discover_fixtures = _STORE.discover_fixtures  # pylint: disable=invalid-name

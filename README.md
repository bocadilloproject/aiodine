# aiodine

[![python](https://img.shields.io/pypi/pyversions/aiodine.svg?logo=python&logoColor=fed749&colorB=3770a0&label=)](https://www.python.org)
[![pypi](https://img.shields.io/pypi/v/aiodine.svg)][pypi-url]
[![travis](https://img.shields.io/travis/bocadilloproject/aiodine.svg)](https://travis-ci.org/bocadilloproject/aiodine)
[![black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/ambv/black)
[![codecov](https://codecov.io/gh/bocadilloproject/aiodine/branch/master/graph/badge.svg)](https://codecov.io/gh/bocadilloproject/aiodine)
[![license](https://img.shields.io/pypi/l/aiodine.svg)][pypi-url]

[pypi-url]: https://pypi.org/project/aiodine/

aiodine provides async-first [dependency injection][di] in the style of [Pytest fixtures](https://docs.pytest.org/en/latest/fixture.html) for Python 3.6+.

- [Installation](#installation)
- [Concepts](#concepts)
- [Usage](#usage)
- [FAQ](#faq)
- [Changelog](#changelog)

## Installation

```
pip install aiodine
```

## Concepts

aiodine revolves around two concepts:

- **Providers** are in charge of setting up, returning and optionally cleaning up _resources_.
- **Consumers** can access these resources by declaring the provider as one of their parameters.

This approach is an implementation of [Dependency Injection][di] and makes providers and consumers:

- **Explicit**: referencing providers by name on the consumer's signature makes dependencies clear and predictable.
- **Modular**: a provider can itself consume other providers, allowing to build ecosystems of reusable (and replaceable) dependencies.
- **Flexible**: provided values are reused within a given scope, and providers and consumers support a variety of syntaxes (asynchronous/synchronous, function/generator) to make provisioning fun again.

aiodine is **async-first** in the sense that:

- It was made to work with coroutine functions and the async/await syntax.
- Consumers can only be called in an asynchronous setting.
- But provider and consumer functions can be regular Python functions and generators too, if only for convenience.

## Usage

### Providers

**Providers** make a _resource_ available to consumers within a certain _scope_. They are created by decorating a **provider function** with `@aiodine.provider`.

Here's a "hello world" provider:

```python
import aiodine

@aiodine.provider
async def hello():
    return "Hello, aiodine!"
```

Providers are available in two **scopes**:

- `function`: the provider's value is re-computed everytime it is consumed.
- `session`: the provider's value is computed only once (the first time it is consumed) and is reused in subsequent calls.

By default, providers are function-scoped.

### Consumers

Once a provider has been declared, it can be used by **consumers**. A consumer is built by decoratinga **consumer function** with `@aiodine.consumer`. A consumer can declare a provider as one of its parameters and aiodine will inject it at runtime.

Here's an example consumer:

```python
@aiodine.consumer
async def show_friendly_message(hello):
    print(hello)

```

All aiodine consumers are asynchronous, so you'll need to run them in an asynchronous context:

```python
from asyncio import run

async def main():
    await show_friendly_message()

run(main())  # "Hello, aiodine!"
```

Of course, a consumer can declare non-provider parameters too. aiodine is smart enough to figure out which parameters should be injected via providers, and which should be expected from the callee.

```python
@aiodine.consumer
async def show_friendly_message(hello, repeat=1):
    for _ in range(repeat):
        print(hello)

async def main():
    await show_friendly_message(repeat=10)
```

### Providers consuming other providers

Providers are modular in the sense that they can themselves consume other providers.

For this to work however, providers need to be _frozen_ first. This ensures that the dependency graph can be correctly resolved regardless of the declaration order.

```python
import aiodine

@aiodine.provider
async def email():
    return "user@example.net"

@aiodine.provider
async def send_email(email):
    print(f"Sending email to {email}…")

aiodine.freeze()  # <- Ensures that `send_email` has resolved `email`.
```

It is safe to call `.freeze()` multiple times.

A context manager syntax is also available:

```python
import aiodine

with aiodine.exit_freeze():
    @aiodine.provider
    async def email():
        return "user@example.net"

    @aiodine.provider
    async def send_email(email):
        print(f"Sending email to {email}…")
```

### Generator providers

Generator providers can be used to perform cleanup (finalization) operations after a provider has gone out of scope.

**Tip**: cleanup code is executed even if an exception occurred in the consumer, so there's no need to surround the `yield` statement with a `try/finally` block.

```python
import os
import aiodine

@aiodine.provider
async def complex_resource():
    print("setting up complex resource…")
    yield "complex"
    print("cleaning up complex resource…")
```

**Note**: session-scoped generator providers will only be cleaned up if using them in the context of a session. See [Sessions](#sessions) for details.

### Lazy async providers

When the provider function is asynchronous, its return value is awaited _before_ being injected into the consumer. In other words, async providers are **eager** by default.

You can mark a provider as **lazy** in order to defer awaiting the provided value to the consumer. This is useful when the provider needs to be conditionally evaluated.

```python
from asyncio import sleep
import aiodine

@aiodine.provider(lazy=True)
async def expensive_computation():
    await sleep(10)
    return 42

@aiodine.consumer
async def compute(expensive_computation, cache=None):
    if cache:
        return cache
    return await expensive_computation
```

### Factory providers

Instead of returning a scalar value, factory providers return a _function_. Factory providers are useful to implement reusable providers that accept a variety of inputs.

> This is a _design pattern_ more than anything else. In fact, there's no extra code in aiodine to support this feature.

The following example defines a factory provider for a (simulated) database query:

```python
import aiodine

@aiodine.provider(scope="session")
async def notes():
    # Some hard-coded sticky notes.
    return [
        {"id": 1, "text": "Groceries"},
        {"id": 2, "text": "Make potatoe smash"},
    ]

@aiodine.provider
async def get_note(notes):
    async def _get_note(pk: int) -> list:
        try:
            # TODO: fetch from a database instead?
            return next(note for note in notes if note["id"] == pk)
        except StopIteration:
            raise ValueError(f"Note with ID {pk} does not exist.")

    return _get_note
```

Example usage in a consumer:

```python
@aiodine.consumer
async def show_note(pk: int, get_note):
    print(await get_note(pk))
```

**Tip**: you can combine factory providers with [generator providers](#generator-providers) to cleanup any resources the factory needs to use. Here's an example that provides temporary files and removes them on cleanup:

```python
import os
import aiodine

@aiodine.provider(scope="session")
def tmpfile():
    files = set()

    async def _create_tmpfile(path: str):
        with open(path, "w") as tmp:
            files.add(path)
            return tmp

    yield _create_tmpfile

    for path in files:
        os.remove(path)
```

### Using providers without declaring them as parameters

Sometimes, a consumer needs to use a provider but doesn't care about the value it returns. In these situations, you can use the `@useprovider` decorator and skip declaring it as a parameter.

**Tip**: the `@useprovider` decorator accepts a variable number of providers, which can be given by name or by reference.

```python
import os
import aiodine

@aiodine.provider
def cache():
    os.makedirs("cache", exist_ok=True)

@aiodine.provider
def debug_log_file():
    with open("debug.log", "w"):
        pass
    yield
    os.remove("debug.log")

@aiodine.consumer
@aiodine.useprovider("cache", debug_log_file)
async def build_index():
    ...
```

### Auto-used providers

Auto-used providers are **automatically activated** (within their configured scope) without having to declare them as a parameter in the consumer.

This can typically spare you from decorating all your consumers with an `@useprovider`.

For example, the auto-used provider below would result in printing the current date and time to the console every time a consumer is called.

```python
import datetime
import aiodine

@aiodine.provider(autouse=True)
async def logdatetime():
    print(datetime.now())
```

### Sessions

A **session** is the context in which _session providers_ live.

More specifically, session providers (resp. generator session providers) are instanciated (resp. setup) when entering a session, and destroyed (resp. cleaned up) when exiting the session.

To enter a session, use:

```python
await aiodine.enter_session()
```

To exit it:

```python
await aiodine.exit_session()
```

An async context manager syntax is also available:

```python
async with aiodine.session():
    ...
```

### Context providers

Context providers were introduced to solve the problem of injecting values that are only defined within a given context (in the sense of asyncio contexts).

#### Example

Consider a waiter that fulfills to orders submitted by customers. Each customer is given with an `Order` object which they can `.write()` their desired items to. This means that the waiter needs to _provide_ an `Order` object to each customer, and then execute the order, and mark it as done.

Here's what the code simulating this situation on the waiter's side may look like:

```python
from asyncio import Queue

import aiodine

class Order:
    def write(self, item: str):
        ...

class Waiter:
    def __init__(self):
        self._order = None
        self.queue = Queue()

        @aiodine.provider
        def order():
            return self._order

    async def execute(self, order: Order):
        ...

    async def serve(self):
        while True:
            # Wait for the next customer to call the waiter…
            customer = self.queue.get()

            # Hand them out an order.
            self._order = Order()
            await customer()

            # Execute the order and mark it as done.
            self.execute(self._order)
            self.queue.task_done()
            self._order = None
```

Customers can write anything on the order they're given. More importantly, they'll probably take some time to think about what they are going to order.

In code, this could translate to:

```python
from asyncio import sleep

@aiodine.consumer
def alice(order: Order):
    # Pondering while looking at the menu…
    await sleep(10)
    order.write("Pizza Margheritta")
```

Let's reflect on this for a second. Noticed how the waiter holds only _one_ reference to an `Order`? This means the code works fine as long as only _one_ customer is served at a time. But what if another custom, say `bob`, comes along while `alice` is pondering? The waiter would modify or delete `alice`'s order before giving a new one to `bob`.

With context providers, we transparently turn the waiter's `order` into a [context variable](https://docs.python.org/3/library/contextvars.html#context-variables) that is local to the context of each customer.

Here's how the code now looks like:

```python
import aiodine

class Waiter:
    def __init__(self):
        self.queue = Queue()
        self.provider = aiodine.create_context_provider("order")

    async def execute(self, order: Order):
        ...

    async def serve(self):
        while True:
            customer = self.queue.get()
            order = Order()
            with self.provider.assign(order=order):
                await customer()
                await self.execute(order)
```

Note:

- Customers can use the `order` provider just like before. In fact, it was created when calling `.create_context_provider()`.
- The `order` is now **context-local**, i.e. its value won't be if other customers come and make orders concurrently.

This situation may look trivial, but it can be found in many implementations of a client/server architecture, including in web frameworks.

#### Usage

To create a context provider, use `aiodine.create_context_provider`. It accepts a variable number of arguments and returns a `ContextProvider`. Each argument is used as the name of a new `@provider` which provides the contents of a `ContextVar` object.

```python
import aiodine

provider = aiodine.create_context_provider("first_name", "last_name")
```

To assign a value to one or more of the declared variables, use the `.assign()` method of the context provider:

```python
with provider.assign(first_name="alice"):
    # Consumers called in this block will receive `"alice"`
    # if they consume the `first_name` provider.
    ...
```

Note: contents of the context variables default to `None`. This means that consumers will receive `None` unless they are called within an `.assign()` block.

## FAQ

### Why "aiodine"?

aiodine contains "aio" as in [asyncio], and "di" as in [Dependency Injection][di]. The last two letters end up making aiodine pronounce like [iodine], the chemical element.

[asyncio]: https://docs.python.org/3/library/asyncio.html
[di]: https://en.wikipedia.org/wiki/Dependency_injection
[iodine]: https://en.wikipedia.org/wiki/Iodine

## Changelog

See [CHANGELOG.md](https://github.com/bocadilloproject/aiodine/blob/master/CHANGELOG.md).

## License

MIT

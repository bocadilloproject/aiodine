# aiodine

[![python](https://img.shields.io/pypi/pyversions/aiodine.svg?logo=python&logoColor=fed749&colorB=3770a0&label=)](https://www.python.org)
[![pypi](https://img.shields.io/pypi/v/aiodine.svg)][pypi-url]
[![travis](https://img.shields.io/travis/bocadilloproject/aiodine.svg)](https://travis-ci.org/bocadilloproject/aiodine)
[![black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/ambv/black)
[![codecov](https://codecov.io/gh/bocadilloproject/aiodine/branch/master/graph/badge.svg)](https://codecov.io/gh/bocadilloproject/aiodine)
[![license](https://img.shields.io/pypi/l/aiodine.svg)][pypi-url]

[pypi-url]: https://pypi.org/project/aiodine/

aiodine provides async-first [dependency injection][di] in the style of [Pytest fixtures](https://docs.pytest.org/en/latest/fixture.html) for Python 3.6+.

## Installation

```
pip install aiodine
```

## Usage

> Note: this section is under construction.

aiodine revolves around two concepts: **providers** and **consumers**.

### Providers

**Providers** make a _resource_ available to consumers within a certain _scope_. They are created by decorating a **provider function** with `@aiodine.provider`.

Here's a "hello world" provider:

```python
import aiodine

@aiodine.provider
async def hello():
    return "Hello, aiodine!"
```

> **Tip**: synchronous provider functions are also supported!

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

> **Tip**: synchronous consumer functions are also supported!

All aiodine consumers are asynchronous, so you'll need to run them in an asynchronous context:

```python
from asyncio import run

async def main():
    await show_friendly_message()

run(main())  # "Hello, aiodine!"
```

A consumer can also define any extra non-provider parameters. These **must** be declared **after** provider parameters in order for aiodine to correctly inject the provided values to the correct parameters. When calling the consumer, extra arguments can be passed as usual.

```python
@aiodine.consumer
async def show_friendly_message(hello, repeat=1):
    for _ in range(repeat):
        print(hello)

async def main():
    await show_friendly_message(repeat=10)
```

### Providers consuming other providers

Providers can also consume other providers. To do so, providers need to be _frozen_ so that the dependency graph can be correctly resolved:

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

A context manager is also available:

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

Note: thanks to this, providers can be declared in any order.

### Generator providers

Generator providers can be used to perform cleanup operations after a provider has gone out of scope.

```python
import os
import aiodine

@aiodine.provider(scope="session")
async def testing():
    initial = os.getenv("APP_ENV")
    os.environ["APP_ENV"] = "TESTING"
    try:
        yield
    finally:
        os.environ.pop("APP_ENV")
        if initial is not None:
            os.environ["APP_ENV"] = initial
```

> **Tip**: synchronous generator providers are also supported!

### Lazy async providers

When the provider function is asynchronous, its return value is awaited _before_ being injected into the consumer. In other words, providers are **eager** by default.

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

## FAQ

### Why "aiodine"?

aiodine contains _aio_ as in _asyncio_, and _di_ as in [Dependency Injection][di] The last two letters are only there to make this library's name pronounce like _iodine_, the chemical element.

[di]: https://en.wikipedia.org/wiki/Dependency_injection

## Changelog

See [CHANGELOG.md](https://github.com/bocadilloproject/aiodine/blob/master/CHANGELOG.md).

## License

MIT

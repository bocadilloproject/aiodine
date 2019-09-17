# aiodine

[![python](https://img.shields.io/pypi/pyversions/aiodine.svg?logo=python&logoColor=fed749&colorB=3770a0&label=)](https://www.python.org)
[![pypi](https://img.shields.io/pypi/v/aiodine.svg)][pypi-url]
[![travis](https://img.shields.io/travis/bocadilloproject/aiodine.svg)](https://travis-ci.org/bocadilloproject/aiodine)
[![black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/ambv/black)
[![codecov](https://codecov.io/gh/bocadilloproject/aiodine/branch/master/graph/badge.svg)](https://codecov.io/gh/bocadilloproject/aiodine)
[![license](https://img.shields.io/pypi/l/aiodine.svg)][pypi-url]

[pypi-url]: https://pypi.org/project/aiodine/

> **Note**: you are currently viewing the development branch for aiodine 2.0. For the documentation from the latest 1.x release, please see the [`latest`] branch.

[`latest`]: https://github.com/bocadilloproject/aiodine/tree/latest

aiodine provides a simple but powerful [dependency injection][di] mechanism for Python 3.6+ asynchronous programs.

**Features**

- Simple and elegant API.
- Setup/teardown logic via async context managers.
- Dependency caching (_coming soon_).
- Great typing support.
- Compatible with asyncio, trio and curio.
- 100% test coverage.
- Fully type-annotated.

**Contents**

- [Quickstart](#quickstart)
- [Installation](#installation)
- [User guide](#user-guide)
- [FAQ](#faq)
- [Changelog](#changelog)

## Quickstart

```python
import aiodine

async def moo() -> str:
    print("What does the cow say?")
    return "moo!"

async def cowsay(what: str = aiodine.depends(moo)):
    print(f"Going to say {what!r}...")
    print(f"Cow says {what}")

import trio
trio.run(aiodine.call_resolved, cowsay)
```

Output:

```console
What does the cow say?
Going to say 'moo!'...
Cow says moo!
```

Running with asyncio or curio instead:

```python
import asyncio
# Python 3.7+
asyncio.run(aiodine.call_resolved(main))
# Python 3.6
loop = asyncio.get_event_loop()
loop.run_until_complete(aiodine.call_resolved(main))

import curio
curio.run(aiodine.call_resolved, (main,))
```

## Installation

```
pip install aiodine
```

## User guide

This section will be using [trio](https://github.com/python-trio/trio) as a concurrency library. Feel free to adapt the code for asyncio or curio.

Let's start with some imports...

```python
import typing
import trio
import aiodine
```

### Core ideas

The core concept in aiodine is that of a **dependable**.

A dependable is created by calling `aiodine.depends(...)`:

```python
async def cowsay(what: str) -> str:
    return f"Cow says {what}"

dependable = aiodine.depends(cowsay)
```

Let's inspect what the dependable refers to:

```python
print(dependable)  # Dependable(func=<function cowsay at ...>)
```

Yup, looks good.

A dependable can't do much on its own — we need to use it along with `call_resolved()`, the main entry point in aiodine.

By default, `call_resolved()` acts as a proxy, i.e. it passes any positional and keyword arguments along to the given function:

```python
async def main() -> str:
    return await aiodine.call_resolved(cowsay, what="moo")

assert trio.run(main) == "Cow says moo"
```

But `call_resolved()` can also _inject_ dependencies into the function it is given. Put differently, `call_resolved()` does all the heavy lifting to provide the function with the arguments it needs.

```python
async def moo() -> str:
    print("Evaluating 'moo()'...")
    await trio.sleep(0.1)  # Simulate some I/O...
    print("Done!")
    return "moo"

async def cowsay(what: str = aiodine.depends(moo)) -> str:
    print(f"cowsay got what={what!r}")
    return f"Cow says {what}"

async def main() -> str:
    # Note that we're leaving out the 'what' argument here.
    return await aiodine.call_resolved(cowsay)

print(trio.run(main)
```

This code will output the following:

```console
Evaluating 'moo()'...
Done!
cowsay got what='moo'
Cow says moo
```

We can still pass arguments from the outside, in which case aiodine won't need to resolve anything.

For example, replace the content of `main()` with:

```python
await aiodine.call_resolved(cowsay, "MOO!!")
```

It should output the following:

```console
cowsay got what='MOO!!'
Cow says MOO!!
```

### Typing support

You may have noticed that we used type annotations in the code snippets above. If you run the snippets through a static type checker such as [mypy](http://mypy-lang.org/), you shouldn't get any errors.

On the other hand, if you change the type hint of `what` to, for example, `int`, then mypy will complain because types don't match anymore:

```python
async def cowsay(what: int = aiodine.depends(moo)) -> str:
    return f"Cow says {what}"
```

```console
Incompatible default for argument "what" (default has type "str", argument has type "int")
```

All of this is by design: aiodine tries to be as type checker-friendly as it can. It even has a test for the above situation!

### Usage with context managers

Sometimes, the dependable has some setup and/or teardown logic associated with it. This is typically the case for most I/O resources such as sockets, files, or database connections.

This is why `aiodine.depends()` also accepts asynchronous context managers:

```python
import typing
import aiodine

# On 3.7+, use `from contextlib import asynccontextmanager`.
from aiodine.compat import asynccontextmanager


class Database:
    def __init__(self, url: str) -> None:
    self.url = url

    async def connect(self) -> None:
        print(f"Connecting to {self.url!r}")

    async def fetchall(self) -> typing.List[dict]:
        print("Fetching data...")
        return [{"id": 1}]

    async def disconnect(self) -> None:
        print(f"Releasing connection to {self.url!r}")


@asynccontextmanager
async def get_db() -> typing.AsyncIterator[Database]:
    db = Database(url="sqlite://:memory:")
    await db.connect()
    try:
        yield db
    finally:
        await db.disconnect()


async def main(db: Database = aiodine.depends(get_db)) -> None:
    rows = await db.fetchall()
    print("Rows:", rows)


trio.run(aiodine.call_resolved, main)
```

This code will output the following:

```console
Connecting to 'sqlite://:memory:'
Fetching data...
Rows: [{'id': 1}]
Releasing connection to 'sqlite://:memory:'
```

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

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

aiodine provides a simple but powerful async-first [dependency injection][di] mechanism for Python 3.6+ programs.

- [Quickstart](#quickstart)
- [Features](#features)
- [Installation](#installation)
- [FAQ](#faq)
- [Changelog](#changelog)

## Quickstart

```python
import asyncio
import typing

from aiodine import call_resolved, depends


class Result(typing.NamedTuple):
    message: str


async def make_api_call() -> Result:
    await asyncio.sleep(0.1)  # Simulate an HTTP request…
    return Result(message="Hello, world!")


async def main(data: Result = depends(make_api_call)) -> None:
    print("Fetched:", data)


asyncio.run(call_resolved(main))  # Fetched: Result(message='Hello, world!')
```

## Features

aiodine is:

- **Editor-friendly**:

In the above example, the `data: Result` annotation allows your editor to provide auto-completion.

- **Type checker-friendly**:

Thanks to the `-> Result` annotation on `make_api_call()`, static type checkers can enforce the consistency of types between the `data` parameter and what `make_api_call()` returns. For example, if we change `data: Result` to `data: dict`, `mypy` will be able to tell that something's wrong.

- **Simple, transparent**:

No complicated concepts, no funky decorators. It just works.

## Installation

```
pip install aiodine
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

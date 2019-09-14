import typing

try:
    from contextlib import nullcontext
except ImportError:
    # Python < 3.7
    from contextlib import contextmanager as _contextmanager

    @_contextmanager  # type: ignore
    def nullcontext() -> typing.Iterator[None]:
        yield

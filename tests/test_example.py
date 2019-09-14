import asyncio
import typing

from aiodine import call_resolved, depends

# Note: on 3.7+, you can use 'from contextlib import asynccontextmanager'.
from aiodine.compat import asynccontextmanager


class APIResult(typing.NamedTuple):
    message: str


# Simple function-based dependable that returns a value.
async def make_api_call() -> APIResult:
    await asyncio.sleep(0.1)  # Simulate an HTTP request…
    return APIResult(message="Hello, world!")


class Database:
    def __init__(self, url: str) -> None:
        self.url = url


# Context manager-based dependables are supported too.
@asynccontextmanager
async def get_db() -> typing.AsyncIterator[Database]:
    db = Database(url="sqlite://:memory:")
    print("Connecting to database")
    try:
        yield db
    finally:
        print("Releasing database connection")


async def main(
    data: APIResult = depends(make_api_call), db: Database = depends(get_db)
) -> None:
    print("Fetched:", data)
    print("Ready to fetch rows in:", db.url)
    # ...


def test_example(capsys: typing.Any) -> None:
    loop = asyncio.new_event_loop()
    loop.run_until_complete(call_resolved(main))
    captured = capsys.readouterr()
    assert captured.out.rstrip("\n").split("\n") == [
        "Connecting to database",
        "Fetched: APIResult(message='Hello, world!')",
        "Ready to fetch rows in: sqlite://:memory:",
        "Releasing database connection",
    ]

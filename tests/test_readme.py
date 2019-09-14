import typing

import pytest
import sniffio


@pytest.mark.anyio
async def test_quickstart(capsys: typing.Any) -> None:
    import aiodine

    async def moo() -> str:
        print("What does the cow say?")
        return "moo!"

    async def cowsay(what: str = aiodine.depends(moo)) -> None:
        print(f"Going to say {what!r}...")
        print(f"Cow says {what}")

    await aiodine.call_resolved(cowsay)

    captured = capsys.readouterr()
    assert captured.out.rstrip("\n").split("\n") == [
        "What does the cow say?",
        "Going to say 'moo!'...",
        "Cow says moo!",
    ]


@pytest.mark.anyio
async def test_usage_with_context_managers(capsys: typing.Any) -> None:
    if sniffio.current_async_library() == "curio":
        pytest.xfail(
            "curio currently disallows async code in 'finally' block "
            "of vanilla async generator"
        )

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

    await aiodine.call_resolved(main)

    captured = capsys.readouterr()
    assert captured.out.rstrip("\n").split("\n") == [
        "Connecting to 'sqlite://:memory:'",
        "Fetching data...",
        "Rows: [{'id': 1}]",
        "Releasing connection to 'sqlite://:memory:'",
    ]

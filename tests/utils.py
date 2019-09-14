import anyio


async def io() -> None:
    """Simulate some kind of I/O call."""
    await anyio.sleep(1e-4)

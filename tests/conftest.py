import pytest
import asyncio


@pytest.fixture()
def loop():
    res = asyncio.new_event_loop()
    yield res
    res.close()

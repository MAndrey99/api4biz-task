import asyncpg
import logging
import os


__all__ = ("pg_engine", "get_db", "asyncpg")
__db: asyncpg.Connection = None


async def pg_engine(app):
    global __db

    logging.info("Подключаемся к базе данных")

    if os.getenv("IS_CONTAINER", False):
        __db = await asyncpg.connect(host="db", user="postgres", database="postgres", password="123")
    else:
        __db = await asyncpg.connect(host="localhost", user="postgres", database="postgres", password="123")

    yield

    await __db.close()


def get_db() -> asyncpg.Connection:
    assert __db
    return __db

import aiohttp
from .util import *
from asyncio import gather
from functools import partial
from typing import Callable, Awaitable


def test_staff(loop):
    async def setup():
        """
        Очищаем все таблицы и создаем компании, к которым будем назначать сотрудников
        """

        async with aiohttp.ClientSession() as session:
            await delete_all(session)
            await check(session, "company/add", {"name": "Google"},    200, empty_schema)
            await check(session, "company/add", {"name": "Apple"},     200, empty_schema)
            await check(session, "company/add", {"name": "JetBrains"}, 200, empty_schema)

    async def _test():
        err_params = [
            {"name": "Tim1", "company": "Apple"},
            {"name": "Tim", "company": "Russia"},
            {"name": "A12"},
            {"name": "Tim"},
            {"name": "New", "id": 17}
        ]

        tasks = []

        async with aiohttp.ClientSession() as session:
            check_add: Callable[[dict, int, dict], Awaitable[dict]] = partial(check, session, "staff/add")
            check_list: Callable[[dict, int, dict], Awaitable[dict]] = partial(check, session, "staff/list", {}, 200,
                                                                               content_schema)

            for p in err_params:
                tasks.append(loop.create_task(check_add(p, 400, error_schema)))

            await gather(*tasks)
            del tasks

            await check_add({"name": "Tim", "company": "Apple"}, 200, empty_schema)
            await check_add({"name": "Tim", "company": "Apple"}, 200, empty_schema)  # У Apple не один Тим
            await check_add({"name": "Sundar", "company": "Google"}, 200, empty_schema)
            await check_add({"name": "Oleg", "company": "JetBrains"}, 200, empty_schema)

            companies = [(i["name"], i["company"]) for i in (await check_list())["content"]]
            assert companies == [("Tim", "Apple"), ("Tim", "Apple"), ("Sundar", "Google"), ("Oleg", "JetBrains")]

    loop.run_until_complete(setup())
    loop.run_until_complete(_test())

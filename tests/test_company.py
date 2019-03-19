import aiohttp
from .util import check as default_check, error_schema, empty_schema, content_schema, delete_all
from asyncio import gather
from functools import partial
from typing import Callable, Awaitable


def test_company(loop):
    async def _test():
        err_params = [
            {"name": "A"},
            {"name": "A12"},
            {"name": "123456"},
            {"name": "New", "id": 17}
        ]

        tasks = []

        async with aiohttp.ClientSession() as session:
            await delete_all(session)

            check_add: Callable[[dict, int, dict], Awaitable[dict]] = partial(default_check, session, "company/add")
            check_list: Callable[[dict, int, dict], Awaitable[dict]] = partial(default_check, session, "company/list",
                                                                               {}, 200, content_schema)

            for p in err_params:
                tasks.append(loop.create_task(check_add(p, 400, error_schema)))

            await gather(*tasks)
            del tasks

            await check_add({"name": "Company"}, 200, empty_schema)
            await check_add({"name": "Company"}, 208, error_schema)
            await check_add({"name": "NewCompany"}, 200, empty_schema)

            companies = [i["name"] for i in (await check_list())["content"]]
            assert companies == ["Company", "NewCompany"]

    loop.run_until_complete(_test())

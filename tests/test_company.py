from asyncio import gather
from functools import partial
from typing import Callable, Awaitable

from .util import *


def test_company(loop):
    company_schema = {
        "type": "object",

        "properties": {
            "name": {"type": "string"}
        },

        "required": ["name"],
        "additionalProperties": False
    }

    async def _test():
        err_params = [
            {"name": "A"},
            {"name": "A12"},
            {"name": "123456"},
            {"name": "New", "id": 17},
            {}
        ]

        tasks = []

        async with aiohttp.ClientSession() as session:
            await delete_all(session)

            check_add:  Callable[[dict, int, dict], Awaitable[dict]] = partial(check, session, "company/add")
            check_list: Callable[[dict, int, dict], Awaitable[dict]] = partial(check, session, "company/list", {}, 200,
                                                                               content_schema)

            for p in err_params:
                tasks.append(loop.create_task(check_add(p, 422, error_schema)))

            await gather(*tasks)
            del tasks

            await check_add({"name": "Company"}, 200, empty_schema)
            await check_add({"name": "Company"}, 208, error_schema)
            await check_add({"name": "NewCompany"}, 200, empty_schema)

            companies = []
            for i in (await check_list())["content"]:
                jsonschema.validate(i, company_schema)
                companies.append(i['name'])
            assert companies == ["Company", "NewCompany"]

    loop.run_until_complete(_test())

from asyncio import gather
from functools import partial

from .util import *


def test_staff(loop):
    person_schema = {
        "type": "object",

        "properties": {
            "name": {
                "type": "string",
                "pattern": "^[A-Z][a-z]+$"
            },
            "companies": {
                "type": "array"
            },
            "id": {
                "type": "integer"
            }
        },

        "required": ["name", "companies", "id"],
        "additionalProperties": False
    }

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
        err_params_and_code = [
            ({"name": "Tim1", "company": "Apple"}, 422),
            ({"name": "Tim", "company": "Russia"}, 400),
            ({"name": "A12"}, 422),
            ({"name": "Tim"}, 422),
            ({"nam": "Tim", "company": "Apple"}, 422),
            ({"company": "Apple"}, 422),
            ({"name": "New", "id": 17}, 422),
            ({}, 422)
        ]

        tasks = []

        async with aiohttp.ClientSession() as session:
            check_addtoc = partial(check, session, "staff/add_to_company")
            check_add = partial(check, session, "staff/add")
            check_list = partial(check, session, "staff/list", {}, 200, content_schema)

            for p, c in err_params_and_code:
                tasks.append(loop.create_task(check_add(p, c, error_schema)))

            await gather(*tasks)
            del tasks

            await check_add({"name": "Tim", "company": "Apple"}, 200, empty_schema)
            await check_add({"name": "Tim", "company": "Apple"}, 200, empty_schema)  # У Apple не один Тим
            await check_add({"name": "Sundar", "company": "Google"}, 200, empty_schema)
            await check_add({"name": "Oleg", "company": "JetBrains"}, 200, empty_schema)

            staff = set()
            oleg_id = None
            for i in (await check_list())["content"]:
                jsonschema.validate(i, person_schema)
                staff.add((i["name"], frozenset(i["companies"])))

                if i["name"] == "Oleg":
                    assert not oleg_id
                    oleg_id = i["id"]

            assert staff == {("Tim", frozenset(("Apple", ))), ("Tim", frozenset(("Apple", ))),
                             ("Sundar", frozenset(("Google", ))), ("Oleg", frozenset(("JetBrains", )))}
            staff = set()

            await check_addtoc({"id": oleg_id, "company": "Google"}, 200, empty_schema)
            await check_addtoc({"id": oleg_id, "company": "Gogle"},  400, error_schema)
            await check_addtoc({"id": 1000,    "company": "Google"}, 400, error_schema)
            del oleg_id

            for i in (await check_list())["content"]:
                jsonschema.validate(i, person_schema)
                staff.add((i["name"], frozenset(i["companies"])))

            assert staff == {("Tim", frozenset(("Apple",))), ("Tim", frozenset(("Apple",))),
                             ("Sundar", frozenset(("Google",))), ("Oleg", frozenset(("JetBrains", "Google",)))}

    loop.run_until_complete(setup())
    loop.run_until_complete(_test())

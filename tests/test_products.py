from asyncio import gather
from functools import partial
from typing import Callable, Awaitable
import dataclasses
import random

from .util import *


@dataclasses.dataclass(frozen=True)
class Product:
    name: str
    employee_id: int = None


product_schema = {
    "type": "object",

    "properties": {
        "name": {
            "type": "string"
        },
        "employee_id": {
            "type": "integer"
        }
    },

    "required": ["name"],
    "additionalProperties": False
}


def test_products(loop):
    async def setup():
        """
        Очищаем все таблицы. создаем компании и сотрудников
        """

        async with aiohttp.ClientSession() as session:
            await delete_all(session)  # очистка таблиц
            get = partial(check, session.get)
            post = partial(check, session.post)

            # добавляем компании
            await post("companies", {"name": "Google"},    200, empty_schema)
            await post("companies", {"name": "Apple"},     200, empty_schema)
            await post("companies", {"name": "JetBrains"}, 200, empty_schema)

            # добавляем людей
            await post("staff", {"name": "Sundar", "company": "Google"},    200, empty_schema)
            await post("staff", {"name": "Tim",    "company": "Apple"},     200, empty_schema)
            await post("staff", {"name": "Oleg",   "company": "JetBrains"}, 200, empty_schema)
            
            # получаем id добавленных людей
            for i in (await get("staff", {}, 200, content_schema))["content"]:
                available_staff_ids.add(i["id"])
            assert len(available_staff_ids) == 3

    async def _test():
        err_params_and_code = [
            ({"name": "product", "employee_id": max(available_staff_ids) + 1}, 400),
            ({"name": "product", "employee_id": "hello!"}, 422),
            ({"name": "Tim", "employee_id": random.choice(available_staff_ids), "add": ""}, 422),
            ({"employee_id": random.choice(available_staff_ids)}, 422),
            ({}, 422)
        ]

        tasks = []

        async with aiohttp.ClientSession() as session:
            check_add: Callable[[dict, int, dict], Awaitable[dict]] = partial(check, session.post, "products")
            check_set: Callable[[dict, int, dict], Awaitable[dict]] = partial(check, session.put, "products")
            check_list: Callable[[dict, int, dict], Awaitable[dict]] = partial(check, session.get, "products", {}, 200,
                                                                               content_schema)

            for p, c in err_params_and_code:
                tasks.append(loop.create_task(check_add(p, c, error_schema)))

            await gather(*tasks)
            del tasks

            await check_add({"name": "p1"}, 200, empty_schema)
            await check_add({"name": "p1"}, 208, error_schema)
            await check_add({"name": "p2"}, 200, empty_schema)
            await check_add({"name": "p3"}, 200, empty_schema)
            await check_add({"name": "p2", "employee_id": 1}, 400, error_schema)

            p4_emp = random.choice(available_staff_ids)
            p2_emp = random.choice(available_staff_ids)
            await check_add({"name": "p4", "employee_id": p4_emp}, 200, empty_schema)
            await check_set({"name": "p2", "employee_id": p2_emp}, 200, empty_schema)

            products = set()
            for i in (await check_list())["content"]:
                jsonschema.validate(i, product_schema)
                products.add(Product(**i))
            assert products == {Product("p1"), Product("p2", p2_emp), Product("p3"), Product("p4", p4_emp)}

    available_staff_ids = set()
    loop.run_until_complete(setup())
    available_staff_ids = list(available_staff_ids)  # там должны быть уникальные элементы
    loop.run_until_complete(_test())

import aiohttp
from random import randint
from asyncio import gather

from .name_generator import NameGenerator


def test_company(loop):
    async def _test():
        ng = NameGenerator()

        async def add_new():
            params = {'name': next(ng)}

            async with session.get('http://0.0.0.0:8080/company/add', params=params) as resp:
                assert resp.status == 200

        async def get_list():
            async with session.get('http://0.0.0.0:8080/company/list') as resp:
                assert resp.status == 200

                for i in (await resp.json())['content']:
                    assert ng.generated(i['name'])

        async with aiohttp.ClientSession() as session:
            tasks = []

            for _ in range(1000):
                tasks.append(loop.create_task(add_new()))
                if randint(0, 5) == 1:
                    tasks.append(loop.create_task(get_list()))

            await gather(*tasks)

    loop.run_until_complete(_test())


def test_add_on_bad_request(loop):
    async def _test():
        async def check(src: str, params: dict):
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://0.0.0.0:8080/{src}/add', params=params) as resp:
                    assert resp.status == 400
                    assert (await resp.json())['error']

        tasks = []

        for src in ("company", "staff", "products"):
            for p in (
                        {"id": randint(0, 1000)},
                        {"employee_id": randint(0, 1000)},
                        {"name": randint(-100, 100), "employee_id": randint(0, 100)},
                        {"name": randint(-100, 100), "id": randint(0, 100)},
                        {"name": "Vi", "id": "err", "employee_id": randint(0, 100)},
                        {"name": "Vi", "id": "err"},
                        {"name": "Vi", "employee_id": "err"},
                        dict()
                    ):
                tasks.append(loop.create_task(check(src, p)))

        await gather(*tasks)

    loop.run_until_complete(_test())

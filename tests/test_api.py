import aiohttp
from random import randint
from asyncio import get_event_loop, gather

from .name_generator import NameGenerator


def test_company():
    async def _test():
        ng = NameGenerator()

        async def add_new():
            params = {'name': next(ng)}

            async with session.get('http://0.0.0.0:8080/company/add', params=params) as resp:
                assert resp.status == 200

        async def get_list():
            async with session.get('http://0.0.0.0:8080/company/list') as resp:
                assert resp.status == 200

                for i in (await resp.text()).split():
                    assert ng.generated(i)

        async with aiohttp.ClientSession() as session:
            tasks = []

            for _ in range(1000):
                tasks.append(loop.create_task(add_new()))
                if randint(0, 5) == 1:
                    tasks.append(loop.create_task(get_list()))

            await gather(*tasks)

    loop = get_event_loop()
    loop.run_until_complete(_test())
    loop.close()

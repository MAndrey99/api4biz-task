import aiohttp
from random import randint
from asyncio import gather
from time import perf_counter

from .util import *
from .name_generator import NameGenerator


def test_many_requests(loop):
    async def _test():
        ng = NameGenerator()

        async with aiohttp.ClientSession() as session:
            await delete_all(session)  # Очищаем все данные перед тестом

            tasks = []

            for _ in range(1000):
                tasks.append(loop.create_task(check(session, "company/add", {'name': next(ng)}, 200, empty_schema)))
                if randint(0, 10) == 1:
                    tasks.append(loop.create_task(check(session, "company/list", {}, 200, content_schema)))

            begin = perf_counter()
            await gather(*tasks)
            t = perf_counter() - begin

            print()
            print(len(tasks), "requests")
            print(f"{t:.3F}s ({t/len(tasks):.6F} s/request)")

    loop.run_until_complete(_test())

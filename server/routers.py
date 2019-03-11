from io import StringIO
from aiohttp.web import RouteTableDef, Request, Response
from .database import get_db, asyncpg
import logging

db: asyncpg.Connection
routers = RouteTableDef()


@routers.get('/company/create')
async def create_company_handler(request: Request):
    name = request.query.get("name")

    if name is None:
        return Response(text="Ошибка! Параметр name не указан!")

    try:
        await db.execute(f"INSERT INTO companies (name) VALUES ('{name}')")
        return Response(text="Success!")
    except asyncpg.UniqueViolationError:
        return Response(text="This company already exists!")


@routers.get('/company/list')
async def create_company_handler(request: Request):
    res = StringIO()

    for i in await db.fetch("SELECT name FROM companies"):
        res.write(f"{i.get('name')}\n")

    return Response(text=res.getvalue())


@routers.get('/')
async def index_handler(request: Request):
    return Response(text="Hello!")


async def init(app):
    global db
    db = get_db()

    logging.info("Добавляем роутеры")
    app.add_routes(routers)

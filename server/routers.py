from io import StringIO
from aiohttp.web import RouteTableDef, Request, Response
from .database import get_db, asyncpg
import logging

db: asyncpg.Connection
routers = RouteTableDef()


@routers.get('/company/add')
async def company_add_handler(request: Request):
    name = request.query.get("name")

    if name is None:
        return Response(text="Ошибка! Параметр name не указан!")

    try:
        await db.execute(f"INSERT INTO companies (name) VALUES ('{name}')")
        return Response(text="Удачно!")
    except asyncpg.UniqueViolationError:
        return Response(text="Эта компания уже существует!")


@routers.get('/company/list')
async def company_list_handler(request: Request):
    res = StringIO()

    for i in await db.fetch("SELECT name FROM companies"):
        res.write(f"{i.get('name')}\n")

    return Response(text=res.getvalue())


@routers.get('/staff/add')
async def staff_add_handler(request: Request):
    name = request.query.get("name")
    company = request.query.get("company")

    if name is None:
        return Response(text="Ошибка! Параметр name не указан!")
    if company is None:
        return Response(text="Ошибка! Параметр company не указан!")

    try:
        await db.execute(f"INSERT INTO staff (name, company_name) VALUES ('{name}', '{company}')")
        return Response(text="Удачно!")
    except asyncpg.ForeignKeyViolationError:
        return Response(text="Указаная компания не существует!")


@routers.get('/staff/list')
async def staff_list_handler(request: Request):
    res = StringIO()

    for i in await db.fetch("SELECT name, company_name FROM staff"):
        res.write(f"{i.get('name')} из {i.get('company_name')}\n")

    return Response(text=res.getvalue())


@routers.get('/')
async def index_handler(request: Request):
    # TODO: print manual
    return Response(text="Hello!")


async def init(app):
    global db
    db = get_db()

    logging.info("Добавляем роутеры")
    app.add_routes(routers)

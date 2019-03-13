from aiohttp.web import RouteTableDef, Request, Response, FileResponse
from io import StringIO
import jsonschema
import logging

from .database import get_db, asyncpg

db_pool: asyncpg.pool.Pool
routers = RouteTableDef()


@routers.get('/company/add')
async def company_add_handler(request: Request):
    """
    Добавляет компанию

    Обязательные параметры:
    - name - название компании
    """

    schema = {
        "type": "object",

        "properties": {
            "name": {
                "type": "string",
                "pattern": "^[A-Za-z]{2,}$"
            },
        },

        "required": ["name"],
        "additionalProperties": False,
    }

    try:
        jsonschema.validate(dict(request.query), schema)
    except jsonschema.ValidationError as e:
        return Response(text=e.message)

    name = request.query.get("name")

    try:
        async with db_pool.acquire() as conn:
            await conn.execute(f"INSERT INTO companies (name) VALUES ('{name}')")
        return Response(text="Удачно!")
    except asyncpg.UniqueViolationError:
        return Response(text="Эта компания уже существует!")


@routers.get('/company/list')
async def company_list_handler(request: Request):
    """
    Возвращает список всех компаний
    """
    async with db_pool.acquire() as conn:
        companies = await conn.fetch("SELECT name FROM companies")

    return Response(text='\n'.join((i.get('name') for i in companies)))


@routers.get('/staff/add')
async def staff_add_handler(request: Request):
    """
    Добавляет работника

    Обязательные параметры:
    - name     - имя работника
    - company  - название компании(Компания должна уже существовать)
    """

    schema = {
        "type": "object",

        "properties": {
            "name": {
                "type": "string",
                "pattern": "^[A-Z][a-z]+$"
            },
            "company": {
                "type": "string",
                "pattern": "^[A-Za-z]{2,}$"
            }
        },

        "additionalProperties": False,
        "minProperties": 2,
    }

    try:
        jsonschema.validate(dict(request.query), schema)
    except jsonschema.ValidationError as e:
        return Response(text=e.message)

    name = request.query.get("name")
    company = request.query.get("company")

    try:
        async with db_pool.acquire() as conn:
            await conn.execute(f"INSERT INTO staff (name, company_name) VALUES ('{name}', '{company}')")
        return Response(text="Удачно!")
    except asyncpg.ForeignKeyViolationError:
        return Response(text="Указаная компания не существует!")


@routers.get('/staff/list')
async def staff_list_handler(request: Request):
    """
    Возвращает список персонала
    """
    async with db_pool.acquire() as conn:
        companies = await conn.fetch("SELECT * FROM staff")

    return Response(text='\n'.join((f"id {i.get('id')}: {i.get('name')} из {i.get('company_name')}" for i in companies)))


@routers.get('/products/add')
async def products_add_handler(request: Request):
    """
    Добавляет продукт

    Обязательные параметры:
    - name         - название продукта

    Дополнительные параметры:
    - employee_id  - id ответственного сотрудника
    """

    schema = {
        "type": "object",

        "properties": {
            "name": {
                "type": "string"
            },
            "employee_id": {
                "type": "string",
                "pattern": "^[0-9]+$"
            }
        },

        "required": ["name"],
        "additionalProperties": False
    }

    try:
        jsonschema.validate(dict(request.query), schema)
    except jsonschema.ValidationError as e:
        return Response(text=e.message)

    name = request.query.get("name")
    employee_id = request.query.get("employee_id")

    async with db_pool.acquire() as conn:
        if employee_id:
            # проверяем, что сотрудник с указанным id существует
            tmp = await conn.fetch(f"SELECT count(*) FROM staff WHERE id={employee_id}")

            if tmp[0].get("count") == 0:
                return Response(text="Ошибка: сотрудника с указанным id не существует!")

            try:
                # добавляем продукт
                await conn.execute(f"INSERT INTO products (name, employee_id) VALUES ('{name}', {employee_id})")
            except asyncpg.UniqueViolationError:
                return Response(text="Ошибка: родукт с этим названием уже существует!")
        else:
            # добавляем продукт без указания отвецственного сотрудника
            async with db_pool.acquire() as conn:
                await conn.execute(f"INSERT INTO products (name) VALUES ('{name}')")
    return Response(text="Удачно!")


@routers.get('/products/set_employee')
async def products_set_employee_handler(request: Request):
    """
    Назначает продукту отвецственного сотрудника

    Обязательные параметры:
    - name         - название продукта
    - employee_id  - id ответственного сотрудника
    """

    schema = {
        "type": "object",

        "properties": {
            "name": {
                "type": "string"
            },
            "employee_id": {
                "type": "string",
                "pattern": "^[0-9]+$"
            }
        },

        "required": ["name", "employee_id"],
        "additionalProperties": False
    }

    try:
        jsonschema.validate(dict(request.query), schema)
    except jsonschema.ValidationError as e:
        return Response(text=e.message)

    name = request.query.get("name")
    employee_id = request.query.get("employee_id")

    if name is None:
        return Response(text="Ошибка! Параметр name не указан!")
    if employee_id is None:
        return Response(text="Ошибка! Параметр employee_id не указан!")

    # проверяем, что сотрудник с указанным id существует
    async with db_pool.acquire() as conn:
        tmp = await conn.fetch(f"SELECT count(*) FROM staff WHERE id={employee_id}")

        if tmp[0].get("count") == 0:
            return Response(text="Ошибка: сотрудника с указанным id не существует!")

        # Обновляем запись
        await conn.execute(f"UPDATE products SET employee_id={employee_id} WHERE name='{name}'")

    return Response(text="Удачно!")


@routers.get('/products/list')
async def products_list_handler(request: Request):
    """
    Возвращает список продуктов
    """
    res = StringIO()

    async with db_pool.acquire() as conn:
        for i in await conn.fetch("SELECT * FROM products"):
            res.write(f"{i.get('name')}")
            if i.get('employee_id'):
                # Получаем имя отвецственного сотрудника
                tmp = await conn.fetch(f"SELECT name FROM staff WHERE id={i.get('employee_id')}")
                assert tmp

                # записываем инфу о сотруднике
                res.write(f" <- {tmp[0].get('name')}(id {i.get('employee_id')})\n")
            else:
                res.write('\n')

    return Response(text=res.getvalue())


@routers.get('/')
async def index_handler(request: Request):
    """
    Возвращает информацию о всех методах api
    """
    return FileResponse("./static/index.html")


async def init(app):
    global db_pool
    db_pool = get_db()

    logging.info("Добавляем роутеры")
    app.add_routes(routers)

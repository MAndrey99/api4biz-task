from aiohttp.web import RouteTableDef, Request, FileResponse
import jsonschema
import logging

from .database import get_db, asyncpg
from .resp_validation import validated_json_response

db_pool: asyncpg.pool.Pool
routers = RouteTableDef()


@routers.get('/delete_all')
async def drop_all_handler(request: Request):
    """
    Удаляет все данные
    """

    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM products")
        await conn.execute("DELETE FROM staff")
        await conn.execute("DELETE FROM companies")

    return validated_json_response({})


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
            }
        },

        "required": ["name"],
        "additionalProperties": False
    }

    try:
        jsonschema.validate(dict(request.query), schema)
    except jsonschema.ValidationError as e:
        return validated_json_response({"error": e.message}, status=422)

    name = request.query.get("name")

    try:
        async with db_pool.acquire() as conn:
            await conn.execute(f"INSERT INTO companies (name) VALUES ('{name}')")
        return validated_json_response({})
    except asyncpg.UniqueViolationError:
        return validated_json_response({"error": "company already created"}, status=208)


@routers.get('/company/list')
async def company_list_handler(request: Request):
    """
    Возвращает список всех компаний
    """
    async with db_pool.acquire() as conn:
        companies = await conn.fetch("SELECT name FROM companies")

    return validated_json_response({
        "content": [{"name": i.get('name')} for i in companies]
    })


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
        "minProperties": 2
    }

    try:
        jsonschema.validate(dict(request.query), schema)
    except jsonschema.ValidationError as e:
        return validated_json_response({"error": e.message}, status=422)

    name = request.query.get("name")
    company = request.query.get("company")

    try:
        async with db_pool.acquire() as conn:
            await conn.execute(f"INSERT INTO staff (name, company_name) VALUES ('{name}', '{company}')")
        return validated_json_response({})
    except asyncpg.ForeignKeyViolationError:
        return validated_json_response({"error": f"company '{company}' is not exists"}, status=400)


@routers.get('/staff/list')
async def staff_list_handler(request: Request):
    """
    Возвращает список персонала
    """
    async with db_pool.acquire() as conn:
        staff = await conn.fetch("SELECT * FROM staff")

    return validated_json_response({
        "content": [
            {
                "id": i.get('id'),
                "name": i.get('name'),
                "company": i.get('company_name')
            } for i in staff
        ]
    })


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
                "pattern": "^[1-9][0-9]*$"
            }
        },

        "required": ["name"],
        "additionalProperties": False
    }

    try:
        jsonschema.validate(dict(request.query), schema)
    except jsonschema.ValidationError as e:
        return validated_json_response({"error": e.message}, status=422)

    name = request.query.get("name")
    employee_id = request.query.get("employee_id")

    async with db_pool.acquire() as conn:
        if employee_id:
            # проверяем, что сотрудник с указанным id существует
            tmp = await conn.fetch(f"SELECT count(*) FROM staff WHERE id={employee_id}")

            if tmp[0].get("count") == 0:
                return validated_json_response({"error": f"employee with id '{employee_id}' is not exists"}, status=400)

            try:
                # добавляем продукт
                await conn.execute(f"INSERT INTO products (name, employee_id) VALUES ('{name}', {employee_id})")
            except asyncpg.UniqueViolationError:
                return validated_json_response({"error": f"product '{name}' already exists"}, status=400)
        else:
            # добавляем продукт без указания отвецственного сотрудника
            async with db_pool.acquire() as conn:
                try:
                    await conn.execute(f"INSERT INTO products (name) VALUES ('{name}')")
                except asyncpg.UniqueViolationError:
                    return validated_json_response({"error": f"product '{name}' already exists"}, status=400)
    return validated_json_response({})


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
        return validated_json_response({"error": e.message}, status=422)

    name = request.query.get("name")
    employee_id = request.query.get("employee_id")

    async with db_pool.acquire() as conn:
        # проверяем, что сотрудник с указанным id существует
        if (await conn.fetch(f"SELECT count(*) FROM staff WHERE id={employee_id}"))[0].get("count") == 0:
            return validated_json_response({"error": f"employee with id '{employee_id}' is not exists"}, status=400)

        # проверяем, что продукт с указанным названием существует
        if (await conn.fetch(f"SELECT count(*) FROM products WHERE name='{name}'"))[0].get("count") == 0:
            return validated_json_response({"error": f"product with name '{name}' is not exists"}, status=400)

        # Обновляем запись
        await conn.execute(f"UPDATE products SET employee_id={employee_id} WHERE name='{name}'")

    return validated_json_response({})


@routers.get('/products/list')
async def products_list_handler(request: Request):
    """
    Возвращает список продуктов
    """

    async with db_pool.acquire() as conn:
        products = await conn.fetch("SELECT * FROM products")

    return validated_json_response({
        "content": [
            {
                "name": i.get('name'),
                "employee_id": i.get('employee_id')
            } for i in products
        ]
    })


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

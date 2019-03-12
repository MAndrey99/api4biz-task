from io import StringIO
from aiohttp.web import RouteTableDef, Request, Response, FileResponse
from .database import get_db, asyncpg
import logging

db: asyncpg.Connection
routers = RouteTableDef()


@routers.get('/company/add')
async def company_add_handler(request: Request):
    """
    Добавляет компанию

    Обязательные параметры:
    - name - название компании
    """

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
    """
    Возвращает список всех компаний
    """
    res = StringIO()

    for i in await db.fetch("SELECT name FROM companies"):
        res.write(f"{i.get('name')}\n")

    return Response(text=res.getvalue())


@routers.get('/staff/add')
async def staff_add_handler(request: Request):
    """
    Добавляет работника

    Обязательные параметры:
    - name     - имя работника
    - company  - название компании(Компания должна уже существовать)
    """
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
    """
    Возвращает список персонала
    """
    res = StringIO()

    for i in await db.fetch("SELECT * FROM staff"):
        res.write(f"id {i.get('id')}: {i.get('name')} из {i.get('company_name')}\n")

    return Response(text=res.getvalue())


@routers.get('/products/add')
async def products_add_handler(request: Request):
    """
    Добавляет продукт

    Обязательные параметры:
    - name         - название продукта

    Дополнительные параметры:
    - employee_id  - id ответственного сотрудника
    """
    name = request.query.get("name")
    employee_id = request.query.get("employee_id")

    if name is None:
        return Response(text="Ошибка! Параметр name не указан!")

    if employee_id:
        # проверяем, что сотрудник с указанным id существует
        tmp = await db.fetch(f"SELECT count(*) FROM staff WHERE id={employee_id}")

        if tmp[0].get("count") == 0:
            return Response(text="Ошибка: сотрудника с указанным id не существует!")

        try:
            # добавляем продукт
            await db.execute(f"INSERT INTO products (name, employee_id) VALUES ('{name}', {employee_id})")
        except asyncpg.UniqueViolationError:
            return Response(text="Ошибка: родукт с этим названием уже существует!")
    else:
        # добавляем продукт без указания отвецственного сотрудника
        await db.execute(f"INSERT INTO products (name) VALUES ('{name}')")
    return Response(text="Удачно!")


@routers.get('/products/set_employee')
async def products_set_employee_handler(request: Request):
    """
    Назначает продукту отвецственного сотрудника

    Обязательные параметры:
    - name         - название продукта
    - employee_id  - id ответственного сотрудника
    """
    name = request.query.get("name")
    employee_id = request.query.get("employee_id")

    if name is None:
        return Response(text="Ошибка! Параметр name не указан!")
    if employee_id is None:
        return Response(text="Ошибка! Параметр employee_id не указан!")

    # проверяем, что сотрудник с указанным id существует
    tmp = await db.fetch(f"SELECT count(*) FROM staff WHERE id={employee_id}")

    if tmp[0].get("count") == 0:
        return Response(text="Ошибка: сотрудника с указанным id не существует!")

    # Обновляем запись
    await db.execute(f"UPDATE products SET employee_id={employee_id} WHERE name='{name}'")

    return Response(text="Удачно!")


@routers.get('/products/list')
async def products_list_handler(request: Request):
    """
    Возвращает список продуктов
    """
    res = StringIO()

    for i in await db.fetch("SELECT * FROM products"):
        res.write(f"{i.get('name')}")
        if i.get('employee_id'):
            # Получаем имя отвецственного сотрудника
            tmp = await db.fetch(f"SELECT name FROM staff WHERE id={i.get('employee_id')}")
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
    global db
    db = get_db()

    logging.info("Добавляем роутеры")
    app.add_routes(routers)

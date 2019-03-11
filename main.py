from aiohttp import web
from server import init as server_init
import logging


app = web.Application()

server_init(app)

logging.info("Сервер запущен")
web.run_app(app)
logging.error("Сервер остановлен")

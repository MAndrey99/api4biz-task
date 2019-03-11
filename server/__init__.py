from aiohttp.web import Application
from .database import pg_engine, get_db
from .routers import routers, init as init_r

import logging
import os

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] module:'%(module)s' line:%(lineno)s - %(message)s",
    datefmt='%m.%d.%Y %H:%M:%S',
    level=logging.ERROR if os.getenv("IS_CONTAINER", False) else logging.INFO
)


def init(app: Application):
    app.cleanup_ctx.append(pg_engine)
    app.on_startup.append(init_r)

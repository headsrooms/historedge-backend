from time import sleep

import uvicorn
from starlette.applications import Starlette
from tortoise.contrib.starlette import register_tortoise

from historedge_backend import settings
from historedge_backend.api.event_handlers import on_startup, on_shutdown
from historedge_backend.api.exception_handlers import exception_handlers
from historedge_backend.api.logger import init_logging
from historedge_backend.api.middleware import middleware
from historedge_backend.api.routes import routes
from historedge_backend.settings import DB_URL

app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
    middleware=middleware,
    exception_handlers=exception_handlers,
    on_startup=on_startup,
    on_shutdown=on_shutdown,
)

init_logging()
sleep(30)
register_tortoise(
    app,
    db_url=DB_URL,
    modules={"models": ["historedge_backend.models"]},
    generate_schemas=settings.GENERATE_SCHEMAS,
)


if __name__ == "__main__":
    uvicorn.run(app)

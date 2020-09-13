import asyncio
from datetime import datetime

import httpx
import pytest
from asgi_lifespan import LifespanManager
from faker import Faker
from starlette.applications import Starlette
from tortoise.contrib.starlette import register_tortoise

from historedge_backend import settings
from historedge_backend.api.exception_handlers import exception_handlers
from historedge_backend.api.middleware import middleware
from historedge_backend.api.routes import routes


@pytest.yield_fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def app_for_httpx():
    app = Starlette(
        debug=settings.DEBUG,
        routes=routes,
        middleware=middleware,
        exception_handlers=exception_handlers,
    )

    register_tortoise(
        app,
        db_url=settings.DB_URL,
        modules={"models": ["models"]},
        generate_schemas=settings.GENERATE_SCHEMAS,
    )

    async with LifespanManager(app):
        yield app


@pytest.fixture(scope="session")
async def base_url():
    yield "http://127.0.0.1:80"


@pytest.fixture(scope="session")
async def app_client(request, app_for_httpx, base_url):
    async with httpx.AsyncClient(app=app_for_httpx, base_url=base_url) as client:
        yield client


@pytest.fixture(scope="session")
async def client(request, base_url):
    async with httpx.AsyncClient(base_url=base_url) as client:
        yield client


@pytest.fixture(scope="session")
async def pages_endpoint(base_url):
    yield f"{base_url}/pages/"


@pytest.fixture
def random_pages():
    faker = Faker()
    Faker.seed(datetime.now().timestamp())
    yield [
        {
            "user_id": "659edd0f-da06-49a7-ae2d-59a3a7955007",
            "url": faker.url(),
            "visited_at": str(faker.date_time()),
        }
        for _ in range(10_000)
    ]


#
# def user_data():
#     faker = Faker()
#     return InputUserSchema(
#         name=faker.first_name(),
#         last_name=faker.last_name(),
#         email=faker.email(),
#         phone=faker.phone_number(),
#     )
#
#
# @pytest.fixture
# async def random_user():
#     customer = await User.create(**user_data().dict())
#     yield customer
#
#     await customer.delete()
#
#
# @pytest.fixture(scope="session", params=[1000])
# async def random_users(request):
#     async def fin():
#         async with in_transaction() as connection:
#             for user in users_db:
#                 await user.delete(using_db=connection)
#
#     users_db = []
#     users = []
#     request.addfinalizer(fin)
#
#     async with in_transaction() as connection:
#         for _ in range(request.param):
#             user_data = user_data()
#             user = User(**asdict(user_data))
#             await user.save(using_db=connection)
#             users_db.append(user)
#             users.append(OutputUserSchema.from_orm(user).dict())
#
#     yield users_db, users

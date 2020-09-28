import asyncio
from time import sleep

from aredis import StrictRedis, ResponseError
from loguru import logger

from historedge_backend import settings

redis = StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

streams = {
    "realtime_pages": ["group"],
    "history_dumps": ["group"],
    "history_chunks": ["group"],
    "pages_to_scrape": ["group"],
}


async def create_streams():
    for stream in streams:
        initial_page = {"opening": "stream"}
        await redis.xadd(stream, initial_page)


async def create_groups():
    consumers = [
        (stream, group) for stream, groups in streams.items() for group in groups
    ]
    for stream, group in consumers:
        try:
            await redis.xgroup_create(stream, group, "$")
        except ResponseError as e:
            if "already exists" not in str(e):
                logger.exception(e)


async def main():
    sleep(10)   # wait for redis
    await create_streams()
    await create_groups()


if __name__ == "__main__":
    asyncio.run(main())

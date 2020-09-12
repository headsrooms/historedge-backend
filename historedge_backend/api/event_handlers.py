import logging

from aredis import ResponseError

from historedge_backend.api.resources import redis

streams = {
    "realtime_pages": ["group"],
    "history_dumps": ["group"],
    "history_chunks": ["group"],
    "pages_to_scrape": ["group"],
}


async def create_stream():
    for stream in streams:
        initial_page = {"opening": "stream"}
        await redis.xadd(stream, initial_page)


async def create_group():
    consumers = [
        (stream, group) for stream, groups in streams.items() for group in groups
    ]
    for stream, group in consumers:
        try:
            await redis.xgroup_create(stream, group, "$")
        except ResponseError as e:
            if "already exists" not in str(e):
                logging.error(e)


on_startup = [create_stream, create_group]
on_shutdown = []

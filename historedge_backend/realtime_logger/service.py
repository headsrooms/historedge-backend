import asyncio
import logging
import sys
from typing import Dict

import uvloop
from pydantic import ValidationError
from tortoise import Tortoise, run_async

from historedge_backend.api.settings import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
)
from historedge_backend.consumer import Consumer
from historedge_backend.events.realtime_pages import PageVisited

DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
REDIS_HOST = "redis"
REDIS_PORT = 6379


class RealtimeLogger(Consumer):
    async def initialize(self):
        logging.info(f"Initializing {str(self)}")
        await Tortoise.init(
            db_url=DB_URL, modules={"models": ["historedge_backend.models"]}
        )

    async def finalize(self):
        logging.info(f"Finalizing {str(self)}")

    async def handle_event(self, event: Dict[bytes, bytes]):
        try:
            page_visited = PageVisited.deserialize(event)
        except ValidationError as e:
            if event and "opening" not in event:
                logging.error(e)
        else:
            asyncio.create_task(page_visited.save())


if __name__ == "__main__":
    worker_id = sys.argv[1]
    uvloop.install()

    logger = RealtimeLogger.create(
        "realtime_pages", "group", f"consumer_{worker_id}", REDIS_HOST, REDIS_PORT
    )
    run_async(logger.run())

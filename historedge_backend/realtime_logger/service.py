import sys
from typing import Dict

import uvloop
from loguru import logger
from pydantic import ValidationError
from tortoise import Tortoise, run_async

from historedge_backend.consumer import Consumer
from historedge_backend.events.realtime_pages import PageVisited
from historedge_backend.settings import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    REDIS_PORT,
    REDIS_HOST,
)

DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class RealtimeLogger(Consumer):
    async def initialize(self):
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.info(f"Initializing {str(self)}")
        await Tortoise.init(
            db_url=DB_URL, modules={"models": ["historedge_backend.models"]}
        )

    async def finalize(self):
        logger.info(f"Finalizing {str(self)}")

    async def handle_event(self, event: Dict[bytes, bytes]):
        try:
            page_visited = PageVisited.deserialize(event)
        except ValidationError as e:
            if event and "opening" not in event:
                logger.exception(str(e))
        else:
            await page_visited.save()


if __name__ == "__main__":
    uvloop.install()

    logger = RealtimeLogger.create("realtime_pages", "group", REDIS_HOST, REDIS_PORT)
    run_async(logger.run())

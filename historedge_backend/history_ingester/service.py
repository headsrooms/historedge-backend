import sys
from typing import Dict

from loguru import logger
from pydantic import ValidationError
from tortoise import Tortoise, run_async

from historedge_backend.consumer import Consumer
from historedge_backend.events.history import HistoryDumpReceived
from historedge_backend.settings import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    REDIS_HOST,
    REDIS_PORT,
)

DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class HistoryIngester(Consumer):
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
            history_dump = HistoryDumpReceived.deserialize(event)
            logger.info(
                "History dump received {dump} n_items:{n_items}",
                dump=history_dump.id,
                n_items=len(history_dump.items),
            )
        except ValidationError as e:
            if event and "opening" not in event:
                logger.exception(str(e))
        else:
            await history_dump.save()


if __name__ == "__main__":
    ingester = HistoryIngester.create("history_chunks", "group", REDIS_HOST, REDIS_PORT)
    run_async(ingester.run())

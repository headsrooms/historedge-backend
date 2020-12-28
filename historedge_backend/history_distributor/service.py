import sys
from typing import Dict, Any, AsyncIterable

import orjson
from aioitertools.more_itertools import chunked
from loguru import logger
from pydantic import ValidationError
from tortoise import Tortoise, run_async
from tortoise.exceptions import DoesNotExist

from historedge_backend.events.history import HistoryDumpReceived
from historedge_backend.intercom import Intercom
from historedge_backend.models import User
from historedge_backend.settings import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    HISTORY_DISTRIBUTOR_CHUNK_LENGTH,
    REDIS_HOST,
    REDIS_PORT,
)

DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class HistoryDistributor(Intercom):
    async def initialize(self):
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.info(f"Initializing {str(self)}")
        await Tortoise.init(
            db_url=DB_URL, modules={"models": ["historedge_backend.models"]}
        )

    async def finalize(self):
        logger.info(f"Finalizing {str(self)}")

    async def handle_event(
        self, event: Dict[bytes, bytes]
    ) -> AsyncIterable[Dict[str, Any]]:
        try:
            history_dump = HistoryDumpReceived.deserialize(event)
            await User.get(id=history_dump.user_id)
        except (ValidationError, AttributeError) as e:
            if event and "opening" not in event:
                logger.exception(str(e))
        except DoesNotExist:
            logger.exception(
                "There is no user with id {user_id}", user_id=history_dump.user_id
            )
        else:
            logger.info(
                "Dump received {dump} n_items:{n_items}",
                dump=history_dump.id,
                n_items=len(history_dump.items),
            )
            history_dump = history_dump.dict()

            async for chunk in chunked(
                history_dump["items"], HISTORY_DISTRIBUTOR_CHUNK_LENGTH
            ):
                chunk = {"user_id": history_dump["user_id"], "items": list(chunk)}
                data = {"data": orjson.dumps(chunk)}
                yield data

            logger.info(
                "Dump distributed {dump} n_items:{n_items}",
                dump=history_dump["id"],
                n_items=len(history_dump["items"]),
            )


if __name__ == "__main__":
    distributor = HistoryDistributor.create(
        "history_dumps", "group", "history_chunks", REDIS_HOST, REDIS_PORT,
    )
    run_async(distributor.run())

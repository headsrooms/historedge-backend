import logging
from typing import Dict, Any, AsyncIterable

import orjson
import uvloop
from aioitertools.more_itertools import chunked
from pydantic import ValidationError
from tortoise import Tortoise, run_async
from tortoise.exceptions import DoesNotExist

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
from historedge_backend.events.history import HistoryDumpReceived
from historedge_backend.intercom import Intercom
from historedge_backend.models import User

DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class HistoryDistributor(Intercom):
    async def initialize(self):
        logging.info(f"Initializing {str(self)}")
        await Tortoise.init(
            db_url=DB_URL, modules={"models": ["historedge_backend.models"]}
        )

    async def finalize(self):
        logging.info(f"Finalizing {str(self)}")

    async def handle_event(
        self, event: Dict[bytes, bytes]
    ) -> AsyncIterable[Dict[str, Any]]:
        try:
            history_dump = HistoryDumpReceived.deserialize(event)
            await User.get(id=history_dump.user_id)
        except (ValidationError, AttributeError) as e:
            if event and "opening" not in event:
                logging.error(e)
        except DoesNotExist:
            logging.error(f"There is no user with id {history_dump.user_id}")
        else:
            logging.info(f"Registering history of user {history_dump.user_id}")
            history_dump = history_dump.dict()
            history_chunks = (
                {"user_id": history_dump["user_id"], "items": list(chunk)}
                for chunk in chunked(history_dump["items"], CHUNK_LENGTH)
            )
            for i, chunk in enumerate(history_chunks):
                data = {"data": orjson.dumps(chunk)}
                yield data

            logging.info(f"Finished history registry of user {history_dump['user_id']}")


if __name__ == "__main__":
    uvloop.install()

    distributor = HistoryDistributor.create(
        "history_dumps",
        "group",
        "history_chunks",
        REDIS_HOST,
        REDIS_PORT,
    )
    run_async(distributor.run())

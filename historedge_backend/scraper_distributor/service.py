import sys
from uuid import uuid4

import orjson
from loguru import logger
from tortoise import Tortoise, run_async

from historedge_backend.models import PageVisit
from historedge_backend.producer import PeriodicProducer
from historedge_backend.settings import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    SCRAPER_DISTRIBUTOR_CHUNK_LENGTH,
    REDIS_HOST,
    REDIS_PORT,
)

DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class ScraperDistributor(PeriodicProducer):
    async def initialize(self):
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.info(f"Initializing {str(self)}")
        await Tortoise.init(
            db_url=DB_URL, modules={"models": ["historedge_backend.models"]}
        )

    async def finalize(self):
        logger.info(f"Finalizing {str(self)}")

    async def create_periodic_event(self):
        page_visits_count = await PageVisit.filter(is_processed=False).count()
        offsets = range(0, page_visits_count, SCRAPER_DISTRIBUTOR_CHUNK_LENGTH)

        if not page_visits_count:
            return

        for offset in offsets:
            page_visits = await (
                PageVisit.filter(is_processed=False)
                .prefetch_related("page")
                .order_by("visited_at")
                .limit(SCRAPER_DISTRIBUTOR_CHUNK_LENGTH)
                .offset(offset)
                .values(id="page__id", url="page__url")
            )

            if page_visits:
                pages = {
                    "id": uuid4(),
                    "items": [
                        {"id": str(page["id"]), "url": page["url"]}
                        for page in page_visits
                    ],
                }

                await self.redis.xadd(
                    self.publish_stream, {"data": orjson.dumps(pages)}
                )
                logger.info(
                    "Batch of pages sent {batch} n_items:{n_items}",
                    batch=pages["id"],
                    n_items=len(pages["items"]),
                )


if __name__ == "__main__":
    distributor = ScraperDistributor.create("pages_to_scrape", REDIS_HOST, REDIS_PORT)
    run_async(distributor.run())

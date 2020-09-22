import orjson
import uvloop
from tortoise import Tortoise, run_async

from loguru import logger

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
from historedge_backend.models import PageVisit
from historedge_backend.producer import PeriodicProducer

DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class ScraperDistributor(PeriodicProducer):
    async def initialize(self):
        logger.info(f"Initializing {str(self)}")
        await Tortoise.init(
            db_url=DB_URL, modules={"models": ["historedge_backend.models"]}
        )

    async def finalize(self):
        logger.info(f"Finalizing {str(self)}")

    async def create_periodic_event(self):
        page_visits_count = await PageVisit.all().count()
        offsets = range(0, page_visits_count, SCRAPER_DISTRIBUTOR_CHUNK_LENGTH)
        for offset in offsets:
            page_visits = await (
                PageVisit.filter(is_processed=False)
                .prefetch_related("page")
                .order_by("visited_at")
                .limit(SCRAPER_DISTRIBUTOR_CHUNK_LENGTH)
                .offset(offset)
                .values(id="page__id", url="page__url")
            )

            pages = [
                {"id": str(page["id"]), "url": page["url"]} for page in page_visits
            ]

            await self.redis.xadd(
                self.publish_stream, {"data": orjson.dumps({"pages": pages})}
            )


if __name__ == "__main__":
    uvloop.install()

    distributor = ScraperDistributor.create("pages_to_scrape", REDIS_HOST, REDIS_PORT)
    run_async(distributor.run())

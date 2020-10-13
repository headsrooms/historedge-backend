import asyncio
import logging
import sys
from dataclasses import dataclass, asdict
from uuid import uuid4

import uvloop
from aredis import StrictRedis
from loguru import logger
from pyppeteer import launch

from historedge_backend.channel import RedisChannel
from historedge_backend.scraper.consumer import ScraperConsumer
from historedge_backend.settings import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    REDIS_HOST,
    REDIS_PORT,
    HEADLESS,
    BROWSER_ARGS,
    SCRAPER_ITEMS_PER_READ,
    SCRAPER_STEALTH,
)

DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


@dataclass
class Scraper:
    subscribe_channel: RedisChannel
    redis: StrictRedis
    consumer: ScraperConsumer = None
    items_per_read: int = 10
    stealth_activated: bool = False

    @classmethod
    def create(
        cls,
        stream: str,
        group: str,
        redis_host: str,
        redis_port: int,
        items_per_read: int = 10,
        stealth_activated: bool = False,
    ):
        consumer = f"{str(cls.__name__)}-{str(uuid4())}"
        redis = StrictRedis(host=redis_host, port=redis_port)
        return cls(
            RedisChannel(stream, group, consumer),
            redis,
            items_per_read=items_per_read,
            stealth_activated=stealth_activated,
        )

    async def initialize(self):
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.info(f"Initializing {str(self)}")
        browser = await launch(
            headless=HEADLESS,
            autoClose=False,
            logLevel=logging.INFO,
            ignoreHTTPSErrors=True,
            args=BROWSER_ARGS,
        )

        self.consumer = ScraperConsumer(
            RedisChannel(**asdict(self.subscribe_channel)),
            self.redis,
            self.items_per_read,
            browser=browser,
            stealth_activated=self.stealth_activated,
        )

    async def finalize(self):
        logger.info(f"Finalizing {str(self)}")

    async def run(self):
        await self.initialize()
        await self.consumer.run()
        await self.finalize()


if __name__ == "__main__":
    uvloop.install()

    scraper = Scraper.create(
        "pages_to_scrape",
        "group",
        REDIS_HOST,
        REDIS_PORT,
        SCRAPER_ITEMS_PER_READ,
        SCRAPER_STEALTH,
    )
    asyncio.run(scraper.run())

import asyncio
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
)

DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/83.0.4103.97 Safari/537.36'

@dataclass
class Scraper:
    subscribe_channel: RedisChannel
    redis: StrictRedis
    consumer: ScraperConsumer = None

    @classmethod
    def create(cls, stream: str, group: str, redis_host: str, redis_port: int):
        consumer = f"{str(cls.__name__)}-{str(uuid4())}"
        redis = StrictRedis(host=redis_host, port=redis_port)
        return cls(RedisChannel(stream, group, consumer), redis)

    async def initialize(self):
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.info(f"Initializing {str(self)}")
        browser = await launch(
            headless=True,
            ignoreHTTPSErrors=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--single-process",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-zygote",
                "--window-position=0,0",
                "--ignore-certificate-errors-spki-list",
                USER_AGENT,
            ],
        )

        self.consumer = ScraperConsumer(
            RedisChannel(**asdict(self.subscribe_channel)), self.redis, browser=browser
        )

    async def finalize(self):
        logger.info(f"Finalizing {str(self)}")

    async def run(self):
        await self.initialize()
        await self.consumer.run()
        await self.finalize()


if __name__ == "__main__":
    uvloop.install()

    scraper = Scraper.create("pages_to_scrape", "group", REDIS_HOST, REDIS_PORT)
    asyncio.run(scraper.run())

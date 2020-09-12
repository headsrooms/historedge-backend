import logging
import sys
from dataclasses import dataclass, asdict

import uvloop
from pyppeteer import launch
from tortoise import run_async

from historedge_backend.api.settings import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
)
from historedge_backend.consumer import RedisChannel
from historedge_backend.scraper.consumer import ScraperConsumer

DB_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
REDIS_HOST = "redis"
REDIS_PORT = 6379


@dataclass
class Scraper:
    subscribe_channel: RedisChannel
    consumer: ScraperConsumer = None

    @classmethod
    def create(cls, stream: str, group: str, consumer: str):
        return cls(RedisChannel(stream, group, consumer))

    async def initialize(self):
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
                '--user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3312.0 Safari/537.36',
            ],
        )
        self.consumer = ScraperConsumer(
            **asdict(self.subscribe_channel), browser=browser
        )

    async def finalize(self):
        logging.info(f"Finalizing {str(self)}")

    async def run(self):
        await self.initialize()
        await self.consumer.run()
        await self.finalize()


if __name__ == "__main__":
    worker_id = sys.argv[1]
    uvloop.install()

    scraper = Scraper.create("pages_to_scrape", "group", f"consumer_{worker_id}")
    run_async(scraper.run())

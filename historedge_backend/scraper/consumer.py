import sys
from dataclasses import dataclass
from typing import Dict

from loguru import logger
from pydantic import ValidationError
from pyppeteer.browser import Browser
from tortoise import Tortoise

from historedge_backend.consumer import Consumer
from historedge_backend.events.pages_to_scrape import PageToScrape
from historedge_backend.settings import DB_URL


@dataclass(frozen=True)
class ScraperConsumer(Consumer):
    browser: Browser = None

    async def initialize(self):
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.info(f"Initializing {str(self)}")
        await Tortoise.init(
            db_url=DB_URL, modules={"models": ["historedge_backend.models"]}
        )

    async def finalize(self):
        logger.info(f"Finalizing {str(self)}")
        await self.browser.close()
        await Tortoise.close_connections()

    async def handle_event(self, event: Dict[bytes, bytes]):
        try:
            page = PageToScrape.deserialize(event)
        except ValidationError as e:
            if event and "opening" not in event:
                logger.exception(str(e))
        else:
            await page.scrape(self.browser, self.stealth_activated)

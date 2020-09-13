import asyncio
import logging
from dataclasses import dataclass
from typing import Dict

from pydantic import ValidationError
from pyppeteer.browser import Browser
from tortoise import Tortoise

from historedge_backend.settings import DB_URL
from historedge_backend.consumer import Consumer
from historedge_backend.events.pages_to_scrape import BatchOfPagesToScrapeReceived


@dataclass(frozen=True)
class ScraperConsumer(Consumer):
    browser: Browser = None

    async def initialize(self):
        logging.info(f"Initializing {str(self)}")
        await Tortoise.init(
            db_url=DB_URL, modules={"models": ["historedge_backend.models"]}
        )

    async def finalize(self):
        logging.info(f"Finalizing {str(self)}")
        await self.browser.close()

    async def handle_event(self, event: Dict[bytes, bytes]):
        try:
            pages = BatchOfPagesToScrapeReceived.deserialize(event)
        except ValidationError as e:
            if event and "opening" not in event:
                logging.error(e)
        else:
            asyncio.create_task(pages.scrape(self.browser))

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict

import Tortoise
from pydantic import ValidationError
from pyppeteer.browser import Browser

from historedge_backend.consumer import Consumer
from historedge_backend.events.pages_to_scrape import BatchOfPagesToScrapeReceived
from historedge_backend.scraper.service import DB_URL


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

    async def handle_event(self, event: Dict[bytes, bytes]):
        try:
            pages = BatchOfPagesToScrapeReceived.deserialize(event)
        except ValidationError as e:
            if event and "opening" not in event:
                logging.error(e)
        else:
            asyncio.create_task(pages.scrape(self.browser))

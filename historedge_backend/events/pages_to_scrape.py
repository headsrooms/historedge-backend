import asyncio
from typing import List, Dict
from uuid import UUID

from loguru import logger
import orjson
from pydantic import BaseModel
from pyppeteer.browser import Browser
from pyppeteer.errors import TimeoutError, PageError, NetworkError
from pyppeteer_stealth import stealth

from historedge_backend.event import RedisEvent
from historedge_backend.models import PageVisit, Page
from historedge_backend.utils import get_text_content, get_links


class PageToScrape(BaseModel):
    id: str
    url: str

    async def save_as_page_visit(self, content: str, links: List[str]):
        links = [(await Page.get_or_create(url=link))[0] for link in links]
        pages = PageVisit.filter(page=self.id, is_processed=False)
        for page in await pages:
            await page.links.add(*links)
        await pages.update(content=content, is_processed=True)


class BatchOfPagesToScrapeReceived(RedisEvent):
    id: UUID
    items: List[PageToScrape]

    async def scrape(self, browser: Browser):
        logger.info("Before scraping {batch} n_items:{n_items}",
                    batch=self.id,
                    n_items=len(self.items))
        for page in self.items:
            try:
                browser_page = await browser.newPage()
                await stealth(browser_page)
                await asyncio.create_task(self.get_page_content(browser_page, page))
            except (TimeoutError, PageError, NetworkError) as e:
                logger.exception(str(e))
        logger.info("Scrape finished {batch} n_items:{n_items}",
                    batch=self.id,
                    n_items=len(self.items))

    @staticmethod
    async def get_page_content(browser: Page, page: PageToScrape):
        await browser.goto(page.url, timeout=0)
        html = await browser.content()
        content = get_text_content(html)
        links = get_links(html)
        await page.save_as_page_visit(content, links)

    @staticmethod
    def convert(data) -> Dict[str, str]:
        """I do this because I have a lot of problems trying to parse json from
        redis, then I send the json object as a string in key of a dict.
        """
        data = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
        data = data.get("data")
        if data:
            return orjson.loads(data)

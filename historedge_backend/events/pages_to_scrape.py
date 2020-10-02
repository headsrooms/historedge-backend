import asyncio
from typing import List, Dict
from uuid import UUID

from loguru import logger
import orjson
from pydantic import BaseModel
from pyppeteer.browser import Browser
from pyppeteer.errors import TimeoutError, PageError, NetworkError
from pyppeteer.page import Page as BrowserPage
from pyppeteer_stealth import stealth

from historedge_backend.event import RedisEvent
from historedge_backend.models import PageVisit, Page
from historedge_backend.utils import get_text_content, get_links


class PageToScrape(BaseModel):
    id: str
    url: str

    async def save_as_page_visit(self, content: str, links: List[str]):
        pages = PageVisit.filter(page=self.id, is_processed=False)

        if links:
            links = [(await Page.get_or_create(url=link))[0] for link in links]
            for page in await pages:
                await page.links.add(*links)

        await pages.update(content=content, is_processed=True)


class BatchOfPagesToScrapeReceived(RedisEvent):
    id: UUID
    items: List[PageToScrape]

    async def scrape(self, browser: Browser):
        logger.info(
            "Before scraping {batch} n_items:{n_items}",
            batch=self.id,
            n_items=len(self.items),
        )

        browser_page = await browser.newPage()
        await stealth(browser_page)
        content_tasks = [self.get_page_content(browser_page, page) for page in self.items]
        try:
            await asyncio.gather(*content_tasks)
        except (TimeoutError, PageError, NetworkError) as e:
            logger.exception(str(e))

        logger.info(
            "Scrape finished {batch} n_items:{n_items}",
            batch=self.id,
            n_items=len(self.items),
        )

    @staticmethod
    async def get_page_content(browser: BrowserPage, page: PageToScrape):
        try:
            await browser.goto(page.url, timeout=0, waitUntil='load')
            await browser.waitForSelector("html")
        except PageError as e:
            logger.error(str(e))
        except TimeoutError as e:
            logger.info(str(e))
        else:
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

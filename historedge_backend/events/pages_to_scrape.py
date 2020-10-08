from typing import List, Dict, NamedTuple
from uuid import UUID

import aiometer
import orjson
from loguru import logger
from pydantic import BaseModel
from pyppeteer.browser import Browser
from pyppeteer.errors import TimeoutError, PageError, NetworkError

from historedge_backend.event import RedisEvent
from historedge_backend.models import PageVisit, Page
from historedge_backend.utils import get_text_content, get_links

MAX_AT_ONCE = 20

BROWSER_TIMEOUT = 25_000
WAIT_AFTER_BROWSE = 3_000


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

        browser_pages = [BrowserAndPage(browser, page) for page in self.items]
        try:
            await aiometer.run_on_each(self.get_page_content, browser_pages, max_at_once=MAX_AT_ONCE)
        except (TimeoutError, PageError, NetworkError) as e:
            logger.exception(str(e))
        except Exception as e:
            logger.exception(str(e))

        logger.info(
            "Scrape finished {batch} n_items:{n_items}",
            batch=self.id,
            n_items=len(self.items),
        )

    @staticmethod
    async def get_page_content(browser_page: "BrowserAndPage"):
        browser, page = browser_page
        browser = await browser.newPage()
        try:
            response = await browser.goto(page.url, timeout=BROWSER_TIMEOUT, waitUntil="networkidle2")
        except PageError as e:
            logger.error(str(e))
        except (TimeoutError, NetworkError) as e:
            logger.info(str(e))
        else:
            if response and response.status < 400:
                await browser.waitFor(WAIT_AFTER_BROWSE)
                html = await browser.content()
                content = get_text_content(html)
                links = get_links(html)
                await page.save_as_page_visit(content, links)
        finally:
            await browser.close()

    @staticmethod
    def convert(data) -> Dict[str, str]:
        """I do this because I have a lot of problems trying to parse json from
        redis, then I send the json object as a string in key of a dict.
        """
        data = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
        data = data.get("data")
        if data:
            return orjson.loads(data)


class BrowserAndPage(NamedTuple):
    browser: Browser
    page: PageToScrape

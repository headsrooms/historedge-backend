from typing import List

from loguru import logger
from playwright import Error
from playwright.async_api import Browser

from historedge_backend.event import RedisEvent
from historedge_backend.models import PageVisit, Page
from historedge_backend.utils import get_text_content, get_links

BROWSER_TIMEOUT = 25_000
WAIT_AFTER_BROWSE = 3_000


class PageToScrape(RedisEvent):
    id: str
    url: str

    async def save_as_failing_page(self, error: str):
        pages = PageVisit.filter(page=self.id, is_processed=False)
        await pages.update(is_processed=True, processing_error=error)

    async def save_as_page_visit(self, content: str, links: List[str]):
        pages = PageVisit.filter(page=self.id, is_processed=False)

        if links:
            links = [(await Page.get_or_create(url=link))[0] for link in links]
            for page in await pages:
                await page.links.add(*links)

        await pages.update(content=content, is_processed=True)

    async def scrape(self, browser: Browser, stealth_activated: bool = False):
        logger.info(
            "Before scraping {id} url:{url}", **self.dict(),
        )

        await self.get_page_content(browser, self, stealth_activated)

        logger.info(
            "Scrape finished {id} url:{url}", **self.dict(),
        )

    @staticmethod
    async def get_page_content(
        browser: Browser, page: "PageToScrape", stealth_activated: bool = False
    ):
        browser_page = await browser.newPage()

        if stealth_activated:
            pass
        try:
            response = await browser_page.goto(page.url, waitUntil="networkidle")
        except Error as e:
            logger.info(str(e))
            await page.save_as_failing_page(str(e))
        else:
            if response and response.status < 400:
                html = await browser_page.content()
                content = get_text_content(html)
                links = get_links(html)
                await page.save_as_page_visit(content, links)
        finally:
            await browser_page.close()

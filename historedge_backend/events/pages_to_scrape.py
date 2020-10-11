from typing import List

from loguru import logger
from pyppeteer.browser import Browser
from pyppeteer.errors import TimeoutError, PageError, NetworkError

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
            "Before scraping {id} url:{url}",
            **self.dict(),
        )

        try:
            await self.get_page_content(browser, self, stealth_activated)
        except (TimeoutError, PageError, NetworkError) as e:
            logger.exception(str(e))
        except Exception as e:
            logger.exception("Exception not caught specifically")
            logger.exception(str(e))

        logger.info(
            "Scrape finished {id} url:{url}",
            **self.dict(),
        )

    @staticmethod
    async def get_page_content(browser_page: "BrowserAndPage"):
        browser, page = browser_page
        browser = await browser.newPage()
        try:
            response = await browser_page.goto(page.url, timeout=BROWSER_TIMEOUT, waitUntil="networkidle2")
        except (TimeoutError, NetworkError, PageError) as e:
            logger.info(str(e))
            await page.save_as_failing_page(str(e))
        else:
            if response and response.status < 400:
                await browser_page.waitFor(WAIT_AFTER_BROWSE)
                html = await browser_page.content()
                content = get_text_content(html)
                links = get_links(html)
                await page.save_as_page_visit(content, links)
        finally:
            await browser_page.close()

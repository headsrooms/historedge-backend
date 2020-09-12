import logging
from datetime import datetime
from json.decoder import JSONDecodeError
from uuid import UUID

from tortoise.exceptions import DoesNotExist

from historedge_backend.api.constants import MALFORMED_JSON_MESSAGE
from historedge_backend.event import RedisEvent
from historedge_backend.models import Page, User, PageVisit


class PageVisited(RedisEvent):
    user_id: UUID
    title: str
    url: str
    content: str
    visited_at: datetime

    async def create(self):
        page, _ = await Page.get_or_create(url=self.url)
        try:
            await User.get(id=self.user_id)
        except DoesNotExist:
            logging.error(f"There is no user with id {self.user_id}")
        except JSONDecodeError:
            logging.error(MALFORMED_JSON_MESSAGE)
        else:
            await PageVisit.get_or_create(
                page_id=page.id,
                user_id=self.user_id,
                visited_at=self.visited_at,
                defaults={"content": self.content, "title": self.title},
            )

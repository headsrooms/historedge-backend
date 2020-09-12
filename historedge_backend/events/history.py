import asyncio
from datetime import datetime, timezone
from typing import List, Dict
from uuid import UUID

import orjson
from pydantic import BaseModel

from historedge_backend.event import RedisEvent
from historedge_backend.models import Page, PageVisit


class HistoryItem(BaseModel):
    id: str
    url: str
    title: str
    lastVisitTime: datetime
    visitCount: int

    async def save(self, user_id: UUID):
        page, _ = await Page.get_or_create(url=self.url)
        await PageVisit.get_or_create(
            page_id=page.id,
            user_id=user_id,
            visited_at=self.lastVisitTime.astimezone(timezone.utc).replace(tzinfo=None),
            defaults={"title": self.title, "is_processed": False},
        )


class HistoryDumpReceived(RedisEvent):
    user_id: UUID
    items: List[HistoryItem]

    async def save(self):
        aws = []
        print(f"Registering a chunk of history of user {self.user_id}")
        for item in self.items:
            aws.append(item.save(self.user_id))
        await asyncio.gather(*aws)
        print(f"Finished to process chunk of history of user {self.user_id}")

    @staticmethod
    def convert(data) -> Dict[str, str]:
        """I do this because I have a lot of problems trying to parse json from
        redis, then I send the json object as a string in key of a dict.
        """
        data = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
        data = data.get("data")
        if data:
            return orjson.loads(data)

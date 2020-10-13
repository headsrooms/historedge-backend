import asyncio
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Tuple, Dict, List, AsyncIterable
from uuid import uuid4

from aredis import StrictRedis

from historedge_backend.channel import RedisChannel


@dataclass(frozen=True)
class Consumer(ABC):
    channel: RedisChannel
    redis: StrictRedis
    items_per_read: int = 10

    @classmethod
    def create(
        cls,
        stream: str,
        group: str,
        redis_host: str,
        redis_port: int,
        items_per_read: int = 10,
    ):
        consumer = f"{str(cls.__name__)}-{str(uuid4())}"
        redis = StrictRedis(host=redis_host, port=redis_port)
        return cls(RedisChannel(stream, group, consumer), redis, items_per_read)

    @abstractmethod
    async def initialize(self):
        pass

    @abstractmethod
    async def finalize(self):
        pass

    @abstractmethod
    async def handle_event(self, event: Dict[bytes, bytes]):
        pass

    async def get_events(self, stream_idx) -> AsyncIterable[Dict[bytes, bytes]]:
        events = await self.redis.xreadgroup(
            self.channel.group, self.channel.consumer, self.items_per_read, **stream_idx
        )
        async for event in self.slice(events):
            yield event

    async def slice(
        self, events: Dict[bytes, List[Tuple[str, Dict[bytes, bytes]]]]
    ) -> AsyncIterable[Dict[bytes, bytes]]:
        events = events.get(self.channel.stream.encode()) or []
        for idx, event in events:
            await self.redis.xack(self.channel.stream, self.channel.group, idx)
            yield event

    async def run(self):
        await self.initialize()
        try:
            stream_idx = {self.channel.stream: ">"}
            while True:
                handle_tasks = []
                async for event in self.get_events(stream_idx):
                    if event:
                        handle_tasks.append(self.handle_event(event))
                if handle_tasks:
                    await asyncio.gather(*handle_tasks)
        finally:
            await self.finalize()

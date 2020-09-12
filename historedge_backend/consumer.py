import asyncio
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Tuple, Dict, List, AsyncIterable

from aredis import StrictRedis


@dataclass(frozen=True)
class RedisChannel:
    stream: str
    group: str
    consumer: str


@dataclass(frozen=True)
class Consumer(ABC):
    channel: RedisChannel
    redis: StrictRedis

    @classmethod
    def create(
        cls, stream: str, group: str, consumer: str, redis_host: str, redis_port: int
    ):
        redis = StrictRedis(host=redis_host, port=redis_port)
        return cls(RedisChannel(stream, group, consumer), redis)

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
            self.channel.group, self.channel.consumer, **stream_idx
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
                async for event in self.get_events(stream_idx):
                    if event:
                        asyncio.create_task(self.handle_event(event))
        finally:
            await self.finalize()

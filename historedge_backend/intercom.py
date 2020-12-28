from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Tuple, Dict, List, Any, AsyncIterable
from uuid import uuid4

from aredis import StrictRedis

from historedge_backend.channel import RedisChannel
from historedge_backend.settings import REDIS_HOST, REDIS_PORT


@dataclass(frozen=True)
class Intercom(ABC):
    subscribe_channel: RedisChannel
    publish_stream: str
    redis: StrictRedis = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)

    @classmethod
    def create(
        cls,
        subscribe_stream: str,
        group: str,
        publish_stream: str,
        redis_host: str,
        redis_port: int,
    ):
        consumer = f"{str(cls.__name__)}-{str(uuid4())}"
        redis = StrictRedis(host=redis_host, port=redis_port)
        subscribe_channel = RedisChannel(subscribe_stream, group, consumer)
        return cls(subscribe_channel, publish_stream, redis)

    @abstractmethod
    async def initialize(self):
        pass

    @abstractmethod
    async def finalize(self):
        pass

    @abstractmethod
    async def handle_event(
        self, event: Dict[bytes, bytes]
    ) -> AsyncIterable[Dict[str, Any]]:
        pass

    async def publish(self, event: Dict[str, Any]):
        await self.redis.xadd(self.publish_stream, event)

    async def get_events(self, stream_idx) -> AsyncIterable[Dict[bytes, bytes]]:
        events = await self.redis.xreadgroup(
            self.subscribe_channel.group, self.subscribe_channel.consumer, **stream_idx
        )
        async for event in self.slice(events):
            yield event

    async def slice(
        self, events: Dict[bytes, List[Tuple[str, Dict[bytes, bytes]]]]
    ) -> AsyncIterable[Dict[bytes, bytes]]:
        events = events.get(self.subscribe_channel.stream.encode()) or []
        for idx, event in events:
            await self.redis.xack(
                self.subscribe_channel.stream, self.subscribe_channel.group, idx
            )
            yield event

    async def run(self):
        await self.initialize()

        try:
            stream_idx = {self.subscribe_channel.stream: ">"}
            while True:
                _ = [
                    await self.publish(event)
                    async for event in self.get_events(stream_idx)
                    async for event in self.handle_event(event)
                    if event
                ]
        finally:
            await self.finalize()

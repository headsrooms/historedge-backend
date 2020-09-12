import asyncio
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Dict, Any

from aredis import StrictRedis

from historedge_backend.api.settings import REDIS_HOST, REDIS_PORT


@dataclass(frozen=True)
class Producer(ABC):
    publish_stream: str
    redis: StrictRedis = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)

    @abstractmethod
    async def initialize(self):
        pass

    @abstractmethod
    async def finalize(self):
        pass

    @abstractmethod
    async def create_event(self) -> Dict[str, Any]:
        pass

    async def publish(self, event: Dict[str, Any]):
        await self.redis.xadd(self.publish_stream, event)

    async def run(self):
        await self.initialize()

        try:
            while True:
                event = await self.create_event()
                await asyncio.create_task(self.publish(event))
        finally:
            await self.finalize()


@dataclass(frozen=True)
class PeriodicProducer(Producer):
    period: float = 3600

    @classmethod
    def create(
        cls, publish_stream: str, redis_host: str, redis_port: int, period: float = 3600
    ):
        redis = StrictRedis(host=redis_host, port=redis_port)
        return cls(publish_stream, redis, period=period)

    @abstractmethod
    async def create_periodic_event(self):
        pass

    async def create_event(self):
        await self.create_periodic_event()
        await asyncio.sleep(self.period)

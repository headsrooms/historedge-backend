from dataclasses import dataclass


@dataclass(frozen=True)
class RedisChannel:
    stream: str
    group: str
    consumer: str

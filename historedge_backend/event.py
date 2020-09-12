from typing import Dict, Any

import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class RedisEvent(BaseModel):
    @staticmethod
    def convert(data) -> Dict[str, str]:
        return {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}

    @classmethod
    def deserialize(cls, event: Dict[bytes, Any]) -> "RedisEvent":
        event = cls.convert(event)
        return cls.parse_obj(event)

    @classmethod
    def serialize(cls, event: Dict[str, str]) -> Dict[str, str]:
        return orjson.loads(cls.parse_obj(event).json())

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps

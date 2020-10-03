from json import JSONDecodeError

import orjson
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import UJSONResponse
from starlette.status import HTTP_201_CREATED

from historedge_backend.api.constants import MALFORMED_JSON_MESSAGE
from historedge_backend.api.resources import redis


async def register_history(request: Request) -> UJSONResponse:
    try:
        history = await request.json()
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    else:
        await redis.xadd("history_dumps", {"data": orjson.dumps(history)})
        return UJSONResponse(
            {"detail": "History received"}, status_code=HTTP_201_CREATED
        )

from json import JSONDecodeError

import orjson
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_201_CREATED

from historedge_backend.api.constants import MALFORMED_JSON_MESSAGE
from historedge_backend.api.resources import redis
from historedge_backend.utils import OrjsonResponse


async def register_history(request: Request) -> OrjsonResponse:
    try:
        history = await request.json()
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    else:
        await redis.xadd("history_dumps", {"data": orjson.dumps(history)})
        return OrjsonResponse(
            {"detail": "History received"}, status_code=HTTP_201_CREATED
        )

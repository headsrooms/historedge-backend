from json import JSONDecodeError

import orjson
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import UJSONResponse
from starlette.status import HTTP_201_CREATED

from historedge_backend.api.constants import MALFORMED_JSON_MESSAGE
from historedge_backend.api.resources import redis
from historedge_backend.events.realtime_pages import PageVisited


async def bookmark_page(request: Request) -> UJSONResponse:
    try:
        page = await request.json()
        response = orjson.loads(PageVisited(**page).json())
        await redis.flushdb()
        await redis.xadd("user_activity", response)

    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    except ValidationError as e:
        raise HTTPException(
            status_code=400, detail=str(e),
        )
    return UJSONResponse(response, status_code=HTTP_201_CREATED)


async def get_bookmarks(request: Request) -> UJSONResponse:
    try:
        page = await request.json()
        response = orjson.loads(PageVisited(**page).json())
        await redis.flushdb()
        await redis.xadd("user_activity", response)

    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    except ValidationError as e:
        raise HTTPException(
            status_code=400, detail=str(e),
        )
    return UJSONResponse(response, status_code=HTTP_201_CREATED)

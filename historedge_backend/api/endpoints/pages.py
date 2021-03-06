from json import JSONDecodeError

import orjson
from loguru import logger
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_201_CREATED

from historedge_backend.api.constants import MALFORMED_JSON_MESSAGE
from historedge_backend.api.resources import redis
from historedge_backend.events.realtime_pages import PageVisited
from historedge_backend.models import Page
from historedge_backend.schemas import OutputPageListSchema
from historedge_backend.utils import OrjsonResponse


async def visit_page(request: Request) -> OrjsonResponse:
    try:
        page = await request.json()
        response = PageVisited.serialize(page)
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    except ValidationError as e:
        logger.error(f"Ignoring request. Cannot serialize {page}")
        logger.exception(str(e))
        raise HTTPException(
            status_code=400, detail="Cannot serialize request",
        )
    else:
        await redis.xadd("realtime_pages", response)
        return OrjsonResponse(response, status_code=HTTP_201_CREATED)


async def get_pages(request: Request) -> OrjsonResponse:
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 10))
    offset = (page - 1) * page_size if page != 1 else 0

    pages = Page.all().limit(page_size).offset(offset)
    count = await Page.all().count()
    pages = await OutputPageListSchema.from_queryset(pages)
    response = orjson.loads(pages.json())
    return OrjsonResponse({"count": count, "pages": response})

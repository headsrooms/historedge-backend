import orjson
from starlette.requests import Request
from starlette.responses import UJSONResponse

from historedge_backend.models import PageVisit
from historedge_backend.schemas import OutputPageVisitListSchema


async def get_page_visits(request: Request) -> UJSONResponse:
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 10))
    offset = (page - 1) * page_size if page != 1 else 0

    pages = PageVisit.all().limit(page_size).offset(offset)
    count = await PageVisit.all().count()
    pages = await OutputPageVisitListSchema.from_queryset(pages)
    response = orjson.loads(pages.json())
    return UJSONResponse({"count": count, "page_visits": response})

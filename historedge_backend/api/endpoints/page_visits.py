import orjson
from starlette.requests import Request
from starlette.responses import UJSONResponse

from historedge_backend.models import PageVisit
from historedge_backend.schemas import OutputPageVisitListSchema


async def get_page_visits(request: Request) -> UJSONResponse:
    is_processed = request.query_params.get("is_processed")
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 10))
    offset = (page - 1) * page_size if page != 1 else 0

    if is_processed:
        is_processed = is_processed == "true" or is_processed == "True"
        pages = PageVisit.filter(is_processed=is_processed)
    else:
        pages = PageVisit.all()
    count = await pages.count()
    pages = pages.limit(page_size).offset(offset)
    pages = await OutputPageVisitListSchema.from_queryset(pages)
    response = orjson.loads(pages.json())
    return UJSONResponse({"count": count, "page_visits": response})

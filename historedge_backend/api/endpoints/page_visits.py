from uuid import uuid4

import orjson
from starlette.requests import Request
from starlette.responses import UJSONResponse
from loguru import logger
from starlette.status import HTTP_201_CREATED

from historedge_backend.api.resources import redis
from historedge_backend.models import PageVisit
from historedge_backend.schemas import OutputPageVisitListSchema
from historedge_backend.settings import SCRAPER_DISTRIBUTOR_CHUNK_LENGTH

PAGES_TO_SCRAPE = "pages_to_scrape"


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


async def distribute_page_visits_to_scraper(request: Request) -> UJSONResponse:
    requested_number_of_pages_to_distribute = int(request.query_params.get("n_pages"))
    number_of_pages_to_distribute = (
        requested_number_of_pages_to_distribute
        or await PageVisit.filter(is_processed=False).count()
    )
    page_length = min(number_of_pages_to_distribute, SCRAPER_DISTRIBUTOR_CHUNK_LENGTH)
    offsets = range(0, number_of_pages_to_distribute, page_length)

    if not number_of_pages_to_distribute:
        return UJSONResponse()

    distributed_items = []
    for offset in offsets:
        page_visits = await (
            PageVisit.filter(is_processed=False)
            .prefetch_related("page")
            .order_by("visited_at")
            .limit(SCRAPER_DISTRIBUTOR_CHUNK_LENGTH)
            .offset(offset)
            .values(id="page__id", url="page__url")
        )

        if page_visits:
            pages = {
                "id": uuid4(),
                "items": [
                    {"id": str(page["id"]), "url": page["url"]} for page in page_visits
                ],
            }

            await redis.xadd(PAGES_TO_SCRAPE, {"data": orjson.dumps(pages)})

            distributed_item = dict(batch=str(pages["id"]), n_items=len(pages["items"]))
            logger.info(
                "Batch of pages sent {batch} n_items:{n_items}", **distributed_item
            )
            distributed_items.append(distributed_item)

    return UJSONResponse(
        {"distributed_items": distributed_items}, status_code=HTTP_201_CREATED
    )

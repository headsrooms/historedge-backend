import orjson
from loguru import logger
from starlette.requests import Request
from starlette.status import HTTP_201_CREATED

from historedge_backend.api.resources import redis
from historedge_backend.models import PageVisit
from historedge_backend.schemas import OutputPageVisitListSchema
from historedge_backend.utils import OrjsonResponse

PAGES_TO_SCRAPE = "pages_to_scrape"


async def get_page_visits(request: Request) -> OrjsonResponse:
    is_processed = request.query_params.get("is_processed")
    without_errors = request.query_params.get("without_errors")
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 10))
    offset = (page - 1) * page_size if page != 1 else 0

    if is_processed or without_errors:
        is_processed = is_processed == "true" or is_processed == "True"
        without_errors = without_errors == "true" or without_errors == "True"
        pages = PageVisit.filter(
            is_processed=is_processed, processing_error__isnull=without_errors
        )
    else:
        pages = PageVisit.all()
    count = await pages.count()
    pages = pages.limit(page_size).offset(offset)
    pages = await OutputPageVisitListSchema.from_queryset(pages)
    response = orjson.loads(pages.json())
    return OrjsonResponse({"count": count, "page_visits": response})


async def distribute_page_visits_to_scraper(request: Request) -> OrjsonResponse:
    requested_number_of_pages_to_distribute = int(request.query_params.get("n_pages"))
    limit = (
        requested_number_of_pages_to_distribute
        or await PageVisit.filter(is_processed=False).count()
    )

    if not limit:
        return OrjsonResponse()

    page_visits = (
        await (
            PageVisit.filter(is_processed=False)
            .prefetch_related("page")
            .order_by("visited_at")
            .limit(limit)
            .values(id="page__id", url="page__url")
        )
        or []
    )

    if page_visits:
        for page in page_visits:
            await redis.xadd(
                PAGES_TO_SCRAPE, {"id": str(page["id"]), "url": page["url"]}
            )

        logger.info("Batch of pages sent n_items:{n_items}", n_items=len(page_visits))

    return OrjsonResponse({"n_items": len(page_visits)}, status_code=HTTP_201_CREATED)

from starlette.exceptions import HTTPException

from historedge_backend.utils import OrjsonResponse


async def http_exception(request, exc):
    return OrjsonResponse({"detail": exc.detail}, status_code=exc.status_code)


exception_handlers = {HTTPException: http_exception}

from starlette.exceptions import HTTPException
from starlette.responses import UJSONResponse


async def http_exception(request, exc):
    return UJSONResponse({"detail": exc.detail}, status_code=exc.status_code)


exception_handlers = {HTTPException: http_exception}

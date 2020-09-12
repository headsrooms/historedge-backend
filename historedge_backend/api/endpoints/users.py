from json import JSONDecodeError

from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_201_CREATED
from tortoise.exceptions import IntegrityError

from historedge_backend.api.constants import MALFORMED_JSON_MESSAGE
from historedge_backend.models import User
from historedge_backend.schemas import InputUserSchema, OutputUserSchema
from historedge_backend.utils import PlainJSONResponse


async def create_user(request: Request) -> PlainJSONResponse:
    try:
        payload = await request.json()
        user_data = InputUserSchema.parse_obj(payload)
        user = await User.create(**user_data.dict())
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail=MALFORMED_JSON_MESSAGE)
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"That email has already been used to create another account",
        )

    response = OutputUserSchema.from_orm(user)
    return PlainJSONResponse(response.json(), status_code=HTTP_201_CREATED)

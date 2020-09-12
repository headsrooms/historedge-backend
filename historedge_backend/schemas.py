from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator

from historedge_backend.models import User, Page, PageVisit

InputUserSchema = pydantic_model_creator(
    User, exclude=("id", "created_at", "modified_at")
)
OutputUserSchema = pydantic_model_creator(User)

OutputPageListSchema = pydantic_queryset_creator(Page)

OutputPageVisitListSchema = pydantic_queryset_creator(PageVisit)

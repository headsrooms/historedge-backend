from tortoise import fields, Model


class User(Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=50)
    last_name = fields.CharField(max_length=50)
    email = fields.CharField(max_length=50, unique=True)
    phone = fields.CharField(max_length=50, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    visits: fields.ReverseRelation["PageVisit"]


class Page(Model):
    id = fields.UUIDField(pk=True)
    url = fields.CharField(max_length=2048)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    visits: fields.ReverseRelation["PageVisit"]
    is_link_of: fields.ManyToManyRelation["PageVisit"]


class PageVisit(Model):
    id = fields.UUIDField(pk=True)
    title = fields.TextField(null=True)
    content = fields.TextField(null=True)
    is_processed = fields.BooleanField(default=True)
    page: fields.ForeignKeyRelation[Page] = fields.ForeignKeyField(
        "models.Page", related_name="visits"
    )
    links: fields.ManyToManyRelation[Page] = fields.ManyToManyField(
        "models.Page", related_name="is_link_of", through="visit_links"
    )
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="visits"
    )
    visited_at = fields.DatetimeField()

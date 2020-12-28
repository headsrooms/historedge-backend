from typing import Any
from typing import List, Optional

import orjson
from selectolax.parser import HTMLParser
from starlette.responses import JSONResponse
from starlette.responses import Response


class PlainJSONResponse(Response):
    media_type = "application/json"


class OrjsonResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return orjson.dumps(content)


def get_links(html: str) -> Optional[List[str]]:
    tree = HTMLParser(html)

    if tree.body:
        select = tree.body.css("a")
        links = [el.attrs.get("href") for el in select]
        links = [link for link in links if link and "http" in link]

        return links


def get_text_content(html) -> Optional[str]:
    tree = HTMLParser(html)

    if tree.body:
        for tag in tree.css("script"):
            tag.decompose()
        for tag in tree.css("style"):
            tag.decompose()

        text = tree.body.text(separator="\n", strip=True)
        return text

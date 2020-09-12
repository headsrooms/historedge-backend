import logging
from asyncio import as_completed

import pytest


@pytest.mark.asyncio
async def test_creating_a_lot_of_pages(client, random_pages, pages_endpoint):
    aws = [client.post(pages_endpoint, json=page) for page in random_pages]

    for coro in as_completed(aws):
        earliest_result = await coro
        logging.debug(earliest_result.json())

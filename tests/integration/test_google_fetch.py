import re

import aiostream
import pytest

from python_quickstart_repo.page_fetcher import AsyncHttpFetcher


@pytest.mark.asyncio
async def test_fetch_google():
    page_fetcher = AsyncHttpFetcher("https://www.google.com/", 1, re.compile(".*google.*"))
    reply_count = 0

    async for reply in aiostream.stream.take(page_fetcher, 3).stream():
        reply_count += 1

        assert reply.status_code == 200
        assert reply.regex_match is True
        assert reply.url == "https://www.google.com/"

    assert reply_count == 3

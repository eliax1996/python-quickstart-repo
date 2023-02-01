import aiostream
import pytest

from python_quickstart_repo.config.page_fetcher_config import PageFetcherConfig
from python_quickstart_repo.http_checkers.page_fetcher import AsyncHttpFetcher


@pytest.mark.asyncio
async def test_fetch_google():
    reply_count = 0
    fetcher_config = PageFetcherConfig(
        url="https://www.google.com/",
        polling_interval_in_seconds=1,
        regex=".*google.*",
        destination_topic="test_topic",
    )

    async with AsyncHttpFetcher(fetcher_config) as page_fetcher:
        async with aiostream.stream.take(page_fetcher, 3).stream() as stream:
            async for (destination_topic, reply) in stream:
                reply_count += 1

                assert reply.status_code in [200, 302]
                assert reply.regex_match is True
                assert reply.url == "https://www.google.com/"
                assert destination_topic == "test_topic"

    assert reply_count == 3

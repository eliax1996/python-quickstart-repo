import re
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from aiostream import stream
from httpx import Response
from mock import mock

from python_quickstart_repo.http_checkers.page_fetcher import AsyncHttpFetcher, HealthCheckReply


def mocked_website_response() -> Response:
    mocked_health_reply: Response = Response(
        status_code=200,
        html="""<!DOCTYPE html>
        <html>
        <body>

        <h1>My awesome page:</h1>

        </body>
        </html>
    """,
    )

    mocked_health_reply.elapsed = timedelta(milliseconds=10)

    return mocked_health_reply


def mocked_website_failed_response() -> Response:
    mocked_health_reply: Response = Response(status_code=500)

    mocked_health_reply.elapsed = timedelta(milliseconds=10)

    return mocked_health_reply


@pytest.mark.asyncio
@mock.patch("asyncio.sleep")
@mock.patch("httpx._client.AsyncClient.get", return_value=mocked_website_response())
async def test_fetch_success(sleep: AsyncMock, http_get: AsyncMock):
    page_fetcher = AsyncHttpFetcher("https://www.mypage.com", 1, re.compile(".*awesome.*"))
    reply_count = 0

    async with stream.take(page_fetcher, 10).stream() as streamer:
        async for reply in streamer:
            reply_count += 1
            assert reply == HealthCheckReply(
                status_code=200,
                response_time=timedelta(microseconds=10000),
                regex_match=True,
                measurement_time=reply.measurement_time,
                url="https://www.mypage.com",
            )

    http_get.assert_called()
    sleep.assert_called()
    assert reply_count == 10


@pytest.mark.asyncio
@mock.patch("asyncio.sleep")
@mock.patch("httpx._client.AsyncClient.get", return_value=mocked_website_failed_response())
async def test_fetch_failure(sleep: AsyncMock, http_get: AsyncMock):
    page_fetcher = AsyncHttpFetcher("https://www.mypage.com", 1, re.compile(".*awesome.*"))
    reply_count = 0

    async with stream.take(page_fetcher, 10).stream() as streamer:
        async for reply in streamer:
            reply_count += 1
            assert reply == HealthCheckReply(
                status_code=500,
                response_time=timedelta(microseconds=10000),
                regex_match=False,
                measurement_time=reply.measurement_time,
                url="https://www.mypage.com",
            )

    http_get.assert_called()
    sleep.assert_called()
    assert reply_count == 10

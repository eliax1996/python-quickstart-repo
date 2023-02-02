import asyncio
import logging
import re
from datetime import datetime
from types import TracebackType
from typing import AsyncContextManager, AsyncIterator, Type

import httpx
from httpx import Response

from python_quickstart_repo.config.page_fetcher_config import PageFetcherConfig
from python_quickstart_repo.datamodels.health_check_reply import HealthCheckReply

TopicWithHealthCheckReply = tuple[str, HealthCheckReply]


class HttpFetcherIterator(AsyncIterator[TopicWithHealthCheckReply]):
    """
    Async http fetcher. It fetches a page every polling_interval seconds and returns a HealthCheckReply.
    Shouldn't be used directly, use HttpFetcher with ContextManager to instantiate it.
    """

    def __init__(self, client: httpx.AsyncClient, page_enter_config: PageFetcherConfig) -> None:
        self.client = client
        self.url = page_enter_config.url
        self.polling_interval = page_enter_config.polling_interval_in_seconds
        self.regex = re.compile(page_enter_config.regex) if page_enter_config.regex else None
        self.destination_topic = page_enter_config.destination_topic
        self.logging = logging.getLogger(__name__)

    def process_reply(self, reply: Response, measurement_time: datetime) -> HealthCheckReply:
        elapsed_time = reply.elapsed
        content = reply.text

        if self.regex:
            matched = re.search(self.regex, content) is not None
            self.logging.debug(f"Regex {self.regex} matched: {matched}")
        else:
            self.logging.debug("Regex isn't set, skipping")
            matched = None

        return HealthCheckReply(
            status_code=reply.status_code,
            response_time=elapsed_time,
            regex_match=matched,
            measurement_time=measurement_time,
            url=self.url,
        )

    async def __anext__(self) -> TopicWithHealthCheckReply:
        await asyncio.sleep(self.polling_interval)
        now = datetime.now()
        self.logging.debug(f"Fetching {self.url}")
        reply = await self.client.get(url=self.url)
        self.logging.debug(f"Processing reply of {self.url}")
        processed_reply = self.process_reply(reply, now)
        self.logging.info(f"Sending the processed reply: {processed_reply}")
        return self.destination_topic, processed_reply

    def __aiter__(self):
        return self


class AsyncHttpFetcher(AsyncContextManager):
    """
    Async http fetcher. It fetches a page every polling_interval seconds and returns a HealthCheckReply.
    This class is supposed to be used as an async context manager.

    Parameters:
        url: the url to fetch
        polling_interval: the interval in seconds between two fetches
        regex: an optional regex to match against the page content

    Example:
    ```python
    url = "https://www.google.com"
    polling_interval = 10
    regex = re.compile("google")
    fetcher_config = PageFetcherConfig(
        url="https://www.google.com",
        polling_interval_in_seconds=30,
        regex="my_regex"
    )

    async with AsyncHttpFetcher(fetcher_config) as fetcher:
        async for reply in fetcher:
            elaborate_healthcheck_reply(reply)
    ```
    """

    def __init__(self, page_fetcher_config: PageFetcherConfig) -> None:
        self.polling_interval = page_fetcher_config.polling_interval_in_seconds
        self.page_fetcher_config = page_fetcher_config
        self.logging = logging.getLogger(__name__)

    async def __aenter__(self):
        self.logging.debug(f"Creating http client for {self.page_fetcher_config.url}")
        self.client = await httpx.AsyncClient().__aenter__()
        self.logging.debug(f"Created http client for {self.page_fetcher_config.url}")
        return HttpFetcherIterator(self.client, self.page_fetcher_config)

    async def __aexit__(
        self, __exc_type: Type[BaseException] | None, __exc_value: BaseException | None, __traceback: TracebackType | None
    ) -> bool | None:
        # generally speaking calling directly magic methods is not allowed, but during the wrapping
        # of an object in an async context manager, calling __aenter__ and __aexit__ is allowed.
        # more info here: https://stackoverflow.com/a/26635947
        await self.client.__aexit__(__exc_type, __exc_value, __traceback)
        self.logging.debug(f"Closed http client for {self.page_fetcher_config.url}")
        return None

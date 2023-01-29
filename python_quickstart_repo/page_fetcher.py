import asyncio
import re
from datetime import datetime
from typing import AsyncIterator, Optional

import httpx
from httpx import Response

from python_quickstart_repo.data_model import HealthCheckReply

AsyncFetcher = AsyncIterator[HealthCheckReply]


class AsyncHttpFetcher(AsyncFetcher):
    def __init__(
        self,
        url: str,
        polling_interval: int,
        validated_regex: Optional[re.Pattern] = None,
    ) -> None:
        self.url = url
        self.polling_interval = polling_interval
        self.regex = validated_regex

    def process_reply(self, reply: Response, measurement_time: datetime) -> HealthCheckReply:
        elapsed_time = reply.elapsed
        content = reply.text

        if self.regex:
            matched = re.search(self.regex, content) is not None
        else:
            matched = None

        return HealthCheckReply(
            status_code=reply.status_code,
            response_time=elapsed_time,
            regex_match=matched,
            measurement_time=measurement_time,
            url=self.url,
        )

    async def __anext__(self) -> HealthCheckReply:
        await asyncio.sleep(self.polling_interval)
        async with httpx.AsyncClient() as client:
            now = datetime.now()
            reply = await client.get(url=self.url)
            return self.process_reply(reply, now)

    def __aiter__(self):
        return self

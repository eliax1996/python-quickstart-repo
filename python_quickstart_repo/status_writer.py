from __future__ import annotations

from abc import abstractmethod
from types import TracebackType
from typing import AsyncContextManager, Type

from aiokafka import AIOKafkaProducer
from aiostream import stream

from python_quickstart_repo.config import KafkaProducerConfig
from python_quickstart_repo.page_fetcher import AsyncFetcher, HealthCheckReply


class FetchProducer:
    @abstractmethod
    async def write(self, *fetchers: AsyncFetcher) -> None:
        pass


class KafkaFetchProducer(AsyncContextManager, FetchProducer):
    def __init__(self, producer_config: KafkaProducerConfig) -> None:
        self._producer_config = producer_config
        self._in_context = False

    async def __aenter__(self) -> KafkaFetchProducer:
        self._in_context = True
        self.producer = AIOKafkaProducer(bootstrap_servers=self._producer_config.bootstrap_servers)
        await self.producer.start()
        return self

    async def __aexit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        self._in_context = False
        await self.producer.stop()
        return None

    @staticmethod
    def serialize(page_fetch_result: HealthCheckReply) -> bytes:
        return page_fetch_result.to_json().encode("ascii")

    async def write(self, *fetchers: AsyncFetcher) -> None:
        assert self._in_context, "KafkaFetchProducer must be used as a context manager"

        async with stream.merge(*fetchers).stream() as page_fetch_results:
            async for page_fetch_result in page_fetch_results:
                await self.producer.send_and_wait(
                    self._producer_config.destination_topic,
                    self.serialize(page_fetch_result),
                )

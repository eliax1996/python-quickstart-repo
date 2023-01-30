from __future__ import annotations

from abc import abstractmethod

from aiokafka import AIOKafkaProducer
from aiostream import stream

from python_quickstart_repo.config.kafka_producer_config import KafkaProducerConfig
from python_quickstart_repo.http_checkers.page_fetcher import AsyncFetcher, HealthCheckReply


class FetchProducer:
    @abstractmethod
    async def write(self, *fetchers: AsyncFetcher) -> None:
        pass


class KafkaFetchProducer(FetchProducer):
    def __init__(self, producer_config: KafkaProducerConfig):
        self._producer_config = producer_config

    @staticmethod
    def serialize(page_fetch_result: HealthCheckReply) -> bytes:
        return page_fetch_result.to_json().encode("ascii")

    async def write(self, *fetchers: AsyncFetcher) -> None:
        async with AIOKafkaProducer(bootstrap_servers=self._producer_config.bootstrap_servers) as producer:
            async with stream.merge(*fetchers).stream() as page_fetch_results:
                async for page_fetch_result in page_fetch_results:
                    await producer.send_and_wait(
                        self._producer_config.destination_topic,
                        self.serialize(page_fetch_result),
                    )

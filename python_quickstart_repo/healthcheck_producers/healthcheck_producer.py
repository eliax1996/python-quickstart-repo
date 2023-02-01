from __future__ import annotations

from abc import abstractmethod
from typing import AsyncIterator

from aiokafka import AIOKafkaProducer
from aiokafka.helpers import create_ssl_context
from aiostream import stream

from python_quickstart_repo.config.kafka_producer_config import KafkaProducerConfig
from python_quickstart_repo.http_checkers.page_fetcher import (
    HealthCheckReply,
    TopicWithHealthCheckReply,
)


class FetchProducer:
    @abstractmethod
    async def write(self, *fetchers: AsyncIterator[TopicWithHealthCheckReply]) -> None:
        pass


class KafkaFetchProducer(FetchProducer):
    def __init__(self, producer_config: KafkaProducerConfig):
        self._producer_config = producer_config

    @staticmethod
    def serialize_string(message: str) -> bytes:
        return message.encode("ascii")

    @staticmethod
    def serialize_value(page_fetch_result: HealthCheckReply) -> bytes:
        return KafkaFetchProducer.serialize_string(page_fetch_result.to_json())

    async def write(self, *fetchers: AsyncIterator[TopicWithHealthCheckReply]) -> None:
        security_params = {}

        if self._producer_config.ssl_security_protocol is not None:
            security_params = {
                "security_protocol": self._producer_config.ssl_security_protocol.security_protocol,
                "ssl_context": create_ssl_context(
                    cafile=self._producer_config.ssl_security_protocol.ssl_cafile,
                    certfile=self._producer_config.ssl_security_protocol.ssl_certfile,
                    keyfile=self._producer_config.ssl_security_protocol.ssl_keyfile
                )
            }


        async with AIOKafkaProducer(
            bootstrap_servers=self._producer_config.bootstrap_servers, **security_params
        ) as producer:
            async with stream.merge(*fetchers).stream() as page_fetch_results:
                async for (destination_topic, page_fetch_result) in page_fetch_results:
                    await producer.send_and_wait(
                        topic=destination_topic,
                        value=self.serialize_value(page_fetch_result),
                        key=self.serialize_string(page_fetch_result.url),
                    )

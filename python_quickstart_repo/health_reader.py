from __future__ import annotations

import json
from abc import abstractmethod
from types import TracebackType
from typing import AsyncContextManager, AsyncIterator, Generic, Type, TypeVar

from aiokafka import AIOKafkaConsumer
from aiostream import stream
from pydantic.tools import parse_obj_as

from python_quickstart_repo.config import KafkaConsumerConfig
from python_quickstart_repo.page_fetcher import AsyncFetcher, HealthCheckReply

T = TypeVar("T")


class HealthCheckConsumer(Generic[T]):
    @abstractmethod
    async def write(self, healthcheck: HealthCheckReply) -> T:
        pass


class KafkaHealthcheckConsumer(AsyncContextManager, AsyncIterator[list[T]], Generic[T]):
    def __init__(
        self,
        consumer_config: KafkaConsumerConfig,
        consumers: list[HealthCheckConsumer[T]] | HealthCheckConsumer[T],
    ) -> None:
        self.consumer = AIOKafkaConsumer(
            consumer_config.source_topic,
            bootstrap_servers=consumer_config.bootstrap_servers,
            group_id=consumer_config.group_id,
            enable_auto_commit=False,
            auto_offset_reset=consumer_config.auto_offset_reset,
        )
        self.consumers = consumers if isinstance(consumers, list) else [consumers]
        self._in_context = False

    async def __aenter__(self) -> KafkaHealthcheckConsumer:
        self._in_context = True
        await self.consumer.start()
        return self

    async def __aexit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        self._in_context = False
        await self.consumer.stop()
        return None

    async def __anext__(self) -> list[T]:
        assert self._in_context, "KafkaFetchProducer must be used as a context manager"

        next = await anext(self.consumer)
        health_check = self.deserialize(next.value)
        consumed = []
        for health_consumer in self.consumers:
            consumer_response = await health_consumer.write(health_check)
            consumed.append(consumer_response)

        return consumed

    @staticmethod
    def deserialize(kafka_message: bytes) -> HealthCheckReply:
        reply_dict = json.loads(kafka_message.decode("ascii"))
        reply = parse_obj_as(HealthCheckReply, reply_dict)
        return reply

    def process(self) -> AsyncFetcher:
        return stream.iterate(self.consumer).map(self.deserialize)

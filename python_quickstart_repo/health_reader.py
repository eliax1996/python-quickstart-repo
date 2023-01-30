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


class HealthcheckIterator(Generic[T], AsyncIterator[list[T]]):

    def __init__(
            self,
            kafka_consumer: AIOKafkaConsumer,
            healthcheck_consumers: list[HealthCheckConsumer[T]]
    ) -> None:
        self.kafka_consumer = kafka_consumer
        self.healthcheck_consumers = healthcheck_consumers

    async def __anext__(self) -> list[T]:
        next = await anext(self.kafka_consumer)
        health_check = self.deserialize(next.value)

        consumed = []
        for health_consumer in self.healthcheck_consumers:
            consumer_response = await health_consumer.write(health_check)
            consumed.append(consumer_response)

        return consumed

    @staticmethod
    def deserialize(kafka_message: bytes) -> HealthCheckReply:
        reply_dict = json.loads(kafka_message.decode("ascii"))
        reply = parse_obj_as(HealthCheckReply, reply_dict)
        return reply

    def process(self) -> AsyncFetcher:
        return stream.iterate(self.kafka_consumer).map(self.deserialize)


class KafkaHealthcheckConsumer(AsyncContextManager):
    def __init__(
            self,
            source_topic_consumer_config: KafkaConsumerConfig,
            healthcheck_consumers: list[HealthCheckConsumer[T]] | HealthCheckConsumer[T],
    ) -> None:
        self.kafka_consumer = AIOKafkaConsumer(
            source_topic_consumer_config.source_topic,
            bootstrap_servers=source_topic_consumer_config.bootstrap_servers,
            group_id=source_topic_consumer_config.group_id,
            enable_auto_commit=False,
            auto_offset_reset=source_topic_consumer_config.auto_offset_reset,
        )
        self.healthcheck_consumers = healthcheck_consumers if isinstance(healthcheck_consumers, list) else [
            healthcheck_consumers]

    async def __aenter__(self) -> HealthcheckIterator[T]:
        await self.kafka_consumer.start()
        return HealthcheckIterator(self.kafka_consumer, self.healthcheck_consumers)

    async def __aexit__(
            self,
            __exc_type: Type[BaseException] | None,
            __exc_value: BaseException | None,
            __traceback: TracebackType | None,
    ) -> bool | None:
        await self.kafka_consumer.stop()
        return None

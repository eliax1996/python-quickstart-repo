import json
from types import TracebackType
from typing import Generic, TypeVar, AsyncIterator, AsyncContextManager, Type

from aiokafka import AIOKafkaConsumer
from aiostream import stream
from pydantic import parse_obj_as

from python_quickstart_repo.config.kafka_consumer_config import KafkaConsumerConfig
from python_quickstart_repo.datamodels.health_check_reply import HealthCheckReply
from python_quickstart_repo.healthcheck_producers.healthcheck_consumer import HealthCheckConsumer
from python_quickstart_repo.http_checkers.page_fetcher import AsyncFetcher

T = TypeVar("T")


class HealthcheckIterator(Generic[T], AsyncIterator[list[T]]):
    """An iterator that consume the kafka topic and process the contained Healthcheck
     messages with one or more HealthCheckConsumer[T].
    Shouldn't be used directly, use KafkaHealthcheckConsumer instead."""

    def __init__(self, kafka_consumer: AIOKafkaConsumer, healthcheck_consumers: list[HealthCheckConsumer[T]]) -> None:
        self.kafka_consumer = kafka_consumer
        self.healthcheck_consumers = healthcheck_consumers

    async def __anext__(self) -> list[T]:
        next = await anext(self.kafka_consumer)
        health_check = self.deserialize(next.value)

        consumed = []
        for health_consumer in self.healthcheck_consumers:
            consumer_response = await health_consumer.consume(health_check)
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
    """
        A client enable the user to extract the HealthChecks from the kafka topic
        and process it with one mor more HealthCheckConsumer[T].

        The class should be used as an async context manager.

    Arguments:
        source_topic_consumer_config: The configuration of the kafka consumer.
        healthcheck_consumers: The consumer that will process the HealthCheckReply.

    Example:
        ```python

        my_consumer1 : HealthCheckConsumer[MyConsumerAck] = MyConsumer1()
        my_consumer2 : HealthCheckConsumer[MyConsumerAck] = MyConsumer2()

        async with KafkaHealthcheckConsumer(my_consumer_config, [my_consumer1, my_consumer2]) as healthcheck_consumer:
            async for consumer_acknowledge in healthcheck_consumer:
                my_fancy_elaboration(consumer_acknowledge)
    """

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
        self.healthcheck_consumers = (
            healthcheck_consumers if isinstance(healthcheck_consumers, list) else [healthcheck_consumers]
        )

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

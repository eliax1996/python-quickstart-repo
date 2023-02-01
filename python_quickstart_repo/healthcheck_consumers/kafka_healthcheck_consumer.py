import json
from types import TracebackType
from typing import AsyncContextManager, AsyncIterator, Generic, Type, TypeVar

from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context
from aiostream import stream
from pydantic import parse_obj_as

from python_quickstart_repo.config.kafka_consumer_config import KafkaConsumerConfig
from python_quickstart_repo.datamodels.health_check_reply import HealthCheckReply
from python_quickstart_repo.healthcheck_consumers.healthcheck_consumer import (
    HealthCheckConsumer,
)

T = TypeVar("T")


class HealthcheckIterator(Generic[T], AsyncIterator[list[T]]):
    """An iterator that consume the kafka topic and process the contained Healthcheck
     messages with one or more HealthCheckConsumer[T].
    Shouldn't be used directly, use KafkaHealthcheckConsumer instead."""

    def __init__(
        self, kafka_consumer: AIOKafkaConsumer, healthcheck_consumers: dict[str, list[HealthCheckConsumer[T]]]
    ) -> None:
        self.kafka_consumer = kafka_consumer
        self.healthcheck_consumers = healthcheck_consumers

    async def __anext__(self) -> list[T]:
        consumed_message = await anext(self.kafka_consumer)
        topic = consumed_message.topic
        consumers = []

        if topic in self.healthcheck_consumers:
            consumers = self.healthcheck_consumers[topic]

        health_check = self.deserialize(consumed_message.value)

        consumed = []
        for health_consumer in consumers:
            consumer_response = await health_consumer.consume(health_check)
            consumed.append(consumer_response)

        return consumed

    @staticmethod
    def deserialize(kafka_message: bytes) -> HealthCheckReply:
        reply_dict = json.loads(kafka_message.decode("ascii"))
        reply = parse_obj_as(HealthCheckReply, reply_dict)
        return reply

    def process(self) -> AsyncIterator[HealthCheckReply]:
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
        healthcheck_consumers: dict[str, list[HealthCheckConsumer[T]]],
    ) -> None:
        security_config = source_topic_consumer_config.ssl_security_protocol
        security_params = {}

        if security_config is not None:
            security_params = {
                "security_protocol": security_config.security_protocol,
                "ssl_context": create_ssl_context(
                    cafile=security_config.ssl_cafile,
                    certfile=security_config.ssl_certfile,
                    keyfile=security_config.ssl_keyfile,
                ),
            }

        self.kafka_consumer = AIOKafkaConsumer(
            *source_topic_consumer_config.source_topics,
            bootstrap_servers=source_topic_consumer_config.bootstrap_servers,
            group_id=source_topic_consumer_config.group_id,
            enable_auto_commit=False,
            auto_offset_reset=source_topic_consumer_config.auto_offset_reset,
            **security_params
        )

        self.healthcheck_consumers = healthcheck_consumers

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

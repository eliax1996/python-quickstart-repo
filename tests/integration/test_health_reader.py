from datetime import datetime, timedelta
from typing import Iterator
from unittest.mock import AsyncMock

import pytest
from aiokafka import ConsumerRecord
from mock import mock

from python_quickstart_repo.config.kafka_consumer_config import KafkaConsumerConfig
from python_quickstart_repo.datamodels.health_check_reply import HealthCheckReply
from python_quickstart_repo.healthcheck_producers.healthcheck_consumer import HealthCheckConsumer
from python_quickstart_repo.healthcheck_producers.kafka_healthcheck_consumer import KafkaHealthcheckConsumer
from tests.util.mocked_helpers import CollectorConsumer


def mocked_reply() -> HealthCheckReply:
    return HealthCheckReply(
        status_code=200,
        response_time=timedelta(milliseconds=100),
        regex_match=True,
        url="https://www.myawesomedomain.com",
        measurement_time=datetime.fromisocalendar(2021, 1, 1),
    )


def mocked_kafka_reply() -> ConsumerRecord:
    encoded_reply = mocked_reply().to_json().encode("ascii")
    return ConsumerRecord(
        topic="source_topic",
        partition=0,
        offset=0,
        timestamp=0,
        timestamp_type=0,
        key=None,
        value=encoded_reply,
        checksum=0,
        serialized_key_size=-1,
        serialized_value_size=0,
        headers=[],
    )


class MockedKafkaConsumer(Iterator[ConsumerRecord]):
    def __init__(self, num_reply) -> None:
        self.num_reply = num_reply

    def __iter__(self):
        return self

    def __next__(self):
        if self.num_reply > 0:
            self.num_reply -= 1
            return mocked_kafka_reply()
        else:
            raise StopIteration


@pytest.mark.asyncio
@mock.patch(
    "aiokafka.consumer.consumer.AIOKafkaConsumer.__anext__",
    side_effect=MockedKafkaConsumer(10),
)
async def test_fetch(send_and_wait: AsyncMock):
    collector_consumer = CollectorConsumer()
    kafka_consumer_config = KafkaConsumerConfig(
        source_topic="source_topic",
        bootstrap_servers=["localhost:9092"],
        group_id="group_id",
        auto_offset_reset="earliest",
    )

    async with KafkaHealthcheckConsumer(kafka_consumer_config, collector_consumer) as consumer:
        async for _ in consumer:
            pass

    send_and_wait.assert_called()
    assert collector_consumer.collected == [mocked_reply() for _ in range(10)]

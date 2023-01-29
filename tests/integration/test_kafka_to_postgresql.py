import asyncio
import itertools
from datetime import datetime, timedelta
from typing import Optional

import aiostream
import asyncpg
import pytest
from pydantic import BaseModel

from python_quickstart_repo.config import (
    KafkaConsumerConfig,
    KafkaProducerConfig,
    PostgresqlProducerConfig,
)
from python_quickstart_repo.data_model import HealthCheckReply
from python_quickstart_repo.health_reader import KafkaHealthcheckConsumer
from python_quickstart_repo.postgresql_writer import PostgresqlWriter
from python_quickstart_repo.status_writer import KafkaFetchProducer
from tests.unit.mocked_helpers import CollectorConsumer, MockedAsyncFetcher


@pytest.mark.asyncio
async def test_writing_and_reading_from_kafka():
    producer_config = KafkaProducerConfig(destination_topic="destination_topic", bootstrap_servers=["localhost:9092"])
    consumer_config = KafkaConsumerConfig(
        source_topic="destination_topic",
        bootstrap_servers=["localhost:9092"],
        group_id="test_group",
        auto_offset_reset="earliest",
    )

    num_messages = 20
    mocked_fetcher1 = MockedAsyncFetcher(seed=43, message_to_generate=num_messages)

    async with KafkaFetchProducer(producer_config) as producer:
        await producer.write(mocked_fetcher1)

    collector_consumer = CollectorConsumer()

    async with KafkaHealthcheckConsumer(consumer_config, collector_consumer) as consumer:
        async for _ in aiostream.stream.take(consumer, num_messages):
            pass
    print(collector_consumer.collected == mocked_fetcher1.reply_list)
    assert len(collector_consumer.collected) == num_messages


class StatefulDatetime:
    def __init__(self) -> None:
        self.num_called = 0
        self.returned: list[datetime] = []

    def __call__(self, *args, **kwds):
        self.num_called += 1
        result = datetime.fromisocalendar(2021, 1, 1) + timedelta(minutes=self.num_called)
        self.returned.append(result)
        return result


class HealthcheckMeasurment(BaseModel):
    url_digest: str
    measurement_time: datetime
    response_time_microseconds: int
    uri: str
    status_code: int
    regex_present: bool
    regex_match: Optional[bool]

    def to_healthcheck_reply(self) -> HealthCheckReply:
        return HealthCheckReply(
            status_code=self.status_code,
            response_time=timedelta(microseconds=self.response_time_microseconds),
            url=self.uri,
            measurement_time=self.measurement_time,
            regex_match=self.regex_match if self.regex_present else None,
        )


@pytest.mark.asyncio
async def test_from_generation_to_postgresql():
    producer_config = KafkaProducerConfig(
        destination_topic="another_destination_topic",
        bootstrap_servers=["localhost:9092"],
    )
    consumer_config = KafkaConsumerConfig(
        source_topic="another_destination_topic",
        bootstrap_servers=["localhost:9092"],
        group_id="test_group",
        auto_offset_reset="earliest",
    )

    num_messages = 20

    mocked_fetcher1 = MockedAsyncFetcher(
        seed=43,
        message_to_generate=num_messages // 2,
        datetime_function=StatefulDatetime(),
    )

    mocked_fetcher2 = MockedAsyncFetcher(
        seed=43,
        message_to_generate=num_messages // 2,
        datetime_function=StatefulDatetime(),
        url="https://www.anotherawesomewebsite.com/",
    )

    async with KafkaFetchProducer(producer_config) as producer:
        await producer.write(mocked_fetcher1, mocked_fetcher2)

    postgress_config = PostgresqlProducerConfig(connection_uri="postgresql://admin:admin@localhost:5432/healthcheck")

    async with PostgresqlWriter(postgress_config) as postgress_writer:
        async with KafkaHealthcheckConsumer(consumer_config, postgress_writer) as consumer:
            async for _ in aiostream.stream.take(consumer, num_messages):
                pass

    postgresql = await asyncpg.connect(postgress_config.connection_uri)
    rows = await postgresql.fetch("SELECT * FROM healthcheck_measurements")

    current_replies = set(
        map(
            lambda record: HealthcheckMeasurment.parse_obj(record).to_healthcheck_reply(),
            rows,
        )
    )
    expected_replies = set(itertools.chain(mocked_fetcher1.reply_list, mocked_fetcher2.reply_list))

    assert len(rows) == num_messages
    assert current_replies == expected_replies

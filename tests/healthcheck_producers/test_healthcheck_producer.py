import itertools
from unittest.mock import AsyncMock, call

import pytest
from mock import mock

from python_quickstart_repo.config.kafka_producer_config import KafkaProducerConfig
from python_quickstart_repo.healthcheck_producers.healthcheck_producer import (
    KafkaFetchProducer,
)
from tests.util.mocked_helpers import MockedAsyncFetcher


@pytest.mark.asyncio
@mock.patch("aiokafka.producer.producer.AIOKafkaProducer.send_and_wait")
async def test_fetch(send_and_wait: AsyncMock):
    destination_topic = "destination_topic"
    mocked_fetcher1 = MockedAsyncFetcher(destination_topic=destination_topic, seed=43, message_to_generate=12)
    mocked_fetcher2 = MockedAsyncFetcher(destination_topic=destination_topic, seed=44, message_to_generate=13)

    config = KafkaProducerConfig(bootstrap_servers=["localhost:9092"])

    await KafkaFetchProducer(config).write(mocked_fetcher1, mocked_fetcher2)

    expected_params = [
        call(
            topic=destination_topic,
            value=KafkaFetchProducer.serialize_value(reply),
            key=KafkaFetchProducer.serialize_string(reply.url),
        )
        for (destination_topic, reply) in itertools.chain(mocked_fetcher1.reply_list, mocked_fetcher2.reply_list)
    ]

    assert send_and_wait.call_args_list == expected_params
    assert send_and_wait.call_count == (mocked_fetcher1.message_to_generate + mocked_fetcher2.message_to_generate)

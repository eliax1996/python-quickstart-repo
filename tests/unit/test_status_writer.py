import itertools
from unittest.mock import AsyncMock, call

import pytest
from mock import mock

from python_quickstart_repo.config import KafkaProducerConfig
from python_quickstart_repo.status_writer import KafkaFetchProducer
from tests.unit.mocked_helpers import MockedAsyncFetcher


@pytest.mark.asyncio
@mock.patch("aiokafka.producer.producer.AIOKafkaProducer.send_and_wait")
async def test_fetch(send_and_wait: AsyncMock):
    mocked_fetcher1 = MockedAsyncFetcher(seed=43, message_to_generate=12)
    mocked_fetcher2 = MockedAsyncFetcher(seed=44, message_to_generate=13)

    config = KafkaProducerConfig(destination_topic="destination_topic", bootstrap_servers=["localhost:9092"])

    async with KafkaFetchProducer(config) as producer:
        await producer.write(mocked_fetcher1, mocked_fetcher2)

    expected_params = [
        call(config.destination_topic, KafkaFetchProducer.serialize(reply))
        for reply in itertools.chain(mocked_fetcher1.reply_list, mocked_fetcher2.reply_list)
    ]

    assert send_and_wait.call_args_list == expected_params
    assert send_and_wait.call_count == (mocked_fetcher1.message_to_generate + mocked_fetcher2.message_to_generate)

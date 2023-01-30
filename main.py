import logging
import re
import sys

from python_quickstart_repo.config.config import Config
from python_quickstart_repo.config.kafka_consumer_config import KafkaConsumerConfig
from python_quickstart_repo.config.kafka_producer_config import KafkaProducerConfig
from python_quickstart_repo.config.postgresql_producer_config import PostgresqlProducerConfig
from python_quickstart_repo.healthcheck_consumers.healthcheck_producer import KafkaFetchProducer
from python_quickstart_repo.healthcheck_producers.kafka_healthcheck_consumer import KafkaHealthcheckConsumer
from python_quickstart_repo.healthcheck_producers.postgresql_healthcheck_consumer import PostgresqlWriter
from python_quickstart_repo.http_checkers.page_fetcher import AsyncHttpFetcher


def kafka_to_postgresql():
    consumer_config = KafkaConsumerConfig()
    postgress_config = PostgresqlProducerConfig()

    # todo: insert asynchronous context stack
    async with PostgresqlWriter(postgress_config) as postgress_writer:
        async with KafkaHealthcheckConsumer(consumer_config, postgress_writer) as consumer:
            async for wrote_messages in consumer:
                for message in wrote_messages:
                    logger.debug(f"Wrote to postgresql a message from {message.url} with code {message.status_code}")


def http_to_kafka():
    kafka_producer_config = KafkaProducerConfig()
    page_fetcher = AsyncHttpFetcher("https://www.mypage.com", 1, re.compile(".*awesome.*"))

    await KafkaFetchProducer(kafka_producer_config).write(page_fetcher)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    config = Config()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        level=logging.DEBUG if config.debug else logging.INFO,
    )

    command_map = {
        "http-to-kafka": http_to_kafka,
        "kafka-to-postgresql": kafka_to_postgresql
    }

    commands = list(command_map.keys())

    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        logger.error(f"Invalid command, Usage: main.py {'|'.join(commands)}")
        sys.exit(1)

    command_map[sys.argv[1]]()

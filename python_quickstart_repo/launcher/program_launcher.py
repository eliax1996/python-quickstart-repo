import argparse
import enum
import logging
import os
from contextlib import AsyncExitStack

from python_quickstart_repo.config.config import WorkingMode
from python_quickstart_repo.config.yaml_config_reader import (
    ConsumerConfig,
    ProducerConfig,
    ProgramConfig,
    load_yaml_configs,
)
from python_quickstart_repo.datamodels.health_check_reply import HealthCheckReply
from python_quickstart_repo.healthcheck_consumers.healthcheck_consumer import (
    HealthCheckConsumer,
)
from python_quickstart_repo.healthcheck_consumers.kafka_healthcheck_consumer import (
    KafkaHealthcheckConsumer,
)
from python_quickstart_repo.healthcheck_consumers.postgresql_healthcheck_consumer import (
    PostgresqlWriter,
)
from python_quickstart_repo.healthcheck_producers.healthcheck_producer import (
    KafkaFetchProducer,
)
from python_quickstart_repo.http_checkers.page_fetcher import AsyncHttpFetcher

logger = logging.getLogger(__name__)


class Command(enum.Enum):
    HTTP_TO_KAFKA = "http-to-kafka"
    KAFKA_TO_POSTGRESQL = "kafka-to-postgresql"


def load_config() -> ProgramConfig:
    parser = argparse.ArgumentParser(description="Healthcheck producer or consumer depending on the argument passed")

    producer_or_consumer_group = parser.add_mutually_exclusive_group(required=True)

    producer_or_consumer_group.add_argument(
        "--producer",
        help="""set this flag to produce healthcheck messages to kafka,
         the list of urls, regex and destination topic must be passed as a YAML file""",
        action="store_true",
    )

    producer_or_consumer_group.add_argument(
        "--consumer",
        help="""set this flag to read healthcheck messages to kafka and write them to postgresql
         the list of source topics and postgresql connection parameters must be passed as a YAML file,
         command line options or as environment variables""",
        action="store_true",
    )

    parser.add_argument(
        "-c", "--config", type=str, help="flag to manually provide the path of the YAML config file to use", required=True
    )

    parser.add_argument("--debug", help="set this flag to obtain more detailed logs", action="store_true")

    args = parser.parse_args()
    config_file_path = os.path.relpath(args.config)

    try:
        config = load_yaml_configs(
            config_file_path,
        )
    except TypeError as e:
        logger.error(
            f"There was an error while loading the config from {config_file_path}, "
            f"there might be additional or missing fields, will now exit"
        )
        raise e
    except FileNotFoundError as e:
        logger.error(
            f"There was an error while loading the config from {config_file_path}, "
            f"please check that the path of the config is correct, will now exit"
        )
        raise e
    else:
        logger.info(f"Successfully loaded config from {config_file_path}")

    if args.debug is True:
        config.general_config.debug = True

    if args.producer is True:
        config.general_config.working_mode = WorkingMode.PRODUCER
    else:
        config.general_config.working_mode = WorkingMode.CONSUMER

    return config


async def consumer_program(consumer_config: ConsumerConfig) -> None:
    async with AsyncExitStack() as stack:

        topic_postgresql_writer_dict: dict[str, list[HealthCheckConsumer[HealthCheckReply]]] = {}

        for topic, postgresql_config_list in consumer_config.topic_postgresql_config_dict.items():
            topic_postgresql_writer_dict[topic] = []
            for postgresql_config in postgresql_config_list:
                postgresql_consumer = await stack.enter_async_context(PostgresqlWriter(postgresql_config))
                topic_postgresql_writer_dict[topic].append(postgresql_consumer)
                logger.debug(f"Created postgresql writer for {postgresql_config.table_name} table")

        kafka_consumer = await stack.enter_async_context(
            KafkaHealthcheckConsumer(consumer_config.kafka_consumer_configs, topic_postgresql_writer_dict)
        )

        logger.debug(f"Starting the consumer with {len(topic_postgresql_writer_dict)} monitored topics")

        async for wrote_messages in kafka_consumer:
            for ack in wrote_messages:
                logger.info(f"Wrote to postgresql a message from {ack.url} with code {ack.status_code}")


async def producer_program(producer_config: ProducerConfig) -> None:
    async with AsyncExitStack() as stack:
        page_fetchers = []
        for page_fetcher_config in producer_config.page_fetcher_configs:
            page_fetcher = await stack.enter_async_context(AsyncHttpFetcher(page_fetcher_config))
            logger.debug(f"Created page fetcher for {page_fetcher_config.url}")
            page_fetchers.append(page_fetcher)

        logger.info(f"Starting the producer with {len(page_fetchers)} page fetchers")
        await KafkaFetchProducer(producer_config.kafka_producer_configs).write(*page_fetchers)

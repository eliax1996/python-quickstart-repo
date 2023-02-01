import logging
from typing import Optional

from pyaml_env import parse_config

from python_quickstart_repo.config.config import GeneralConfig
from python_quickstart_repo.config.kafka_consumer_config import KafkaConsumerConfig
from python_quickstart_repo.config.kafka_producer_config import KafkaProducerConfig
from python_quickstart_repo.config.page_fetcher_config import PageFetcherConfig
from python_quickstart_repo.config.postgresql_producer_config import PostgresqlProducerConfig


class ConsumerConfig():
    """Container for the Consumer Configs"""

    def __init__(
            self,
            kafka_consumer_config: KafkaConsumerConfig,
            topic_postgresql_config_dict: dict[str, list[PostgresqlProducerConfig]]
    ):
        self.kafka_consumer_configs = kafka_consumer_config
        self.topic_postgresql_config_dict = topic_postgresql_config_dict

    def __eq__(self, other):
        return isinstance(other, ConsumerConfig) and \
               self.kafka_consumer_configs == other.kafka_consumer_configs and \
               self.topic_postgresql_config_dict == other.topic_postgresql_config_dict

    def __repr__(self):
        return f"ConsumerConfig({self.kafka_consumer_configs}, {self.topic_postgresql_config_dict})"


class ProducerConfig():
    """Container for the Producer Configs"""

    def __init__(
            self,
            kafka_producer_config: KafkaProducerConfig,
            page_fetcher_configs: list[PageFetcherConfig]
    ):
        self.kafka_producer_configs = kafka_producer_config
        self.page_fetcher_configs = page_fetcher_configs

    def __eq__(self, other):
        return isinstance(other, ProducerConfig) and \
               self.kafka_producer_configs == other.kafka_producer_configs and \
               self.page_fetcher_configs == other.page_fetcher_configs

    def __repr__(self):
        return f"ProducerConfig({self.kafka_producer_configs}, {self.page_fetcher_configs})"


class ProgramConfig():
    """Container for all configs"""

    def __init__(
            self,
            general_config: GeneralConfig,
            consumer_config: Optional[ConsumerConfig],
            producer_config: Optional[ProducerConfig]
    ):
        self.general_config = general_config
        self.producer_config = producer_config
        self.consumer_config = consumer_config

    def __eq__(self, other):
        return isinstance(other, ProgramConfig) and \
               self.general_config == other.general_config and \
               self.producer_config == other.producer_config and \
               self.consumer_config == other.consumer_config

    def __repr__(self):
        return f"ProgramConfig({self.general_config}, {self.producer_config}, {self.consumer_config})"


def load_yaml_configs(config_path: Optional[str]) -> ProgramConfig:
    logger = logging.getLogger(__name__)

    config_path = config_path or "config.yaml"

    config = parse_config(config_path)

    general_config = GeneralConfig.parse_obj(config)

    producer_config: Optional[ProducerConfig] = None
    consumer_config: Optional[ConsumerConfig] = None

    if "healthcheck-producer-config" in config:
        producer_config_dict = config["healthcheck-producer-config"]

        kafka_producer_config = KafkaProducerConfig.parse_obj(producer_config_dict)
        page_fetcher_configs: list[PageFetcherConfig] = []
        for website_config in producer_config_dict["websites"]:
            fetcher_config = PageFetcherConfig.parse_obj(website_config)
            page_fetcher_configs.append(fetcher_config)

        producer_config = ProducerConfig(kafka_producer_config, page_fetcher_configs)
        logger.info(f"Loaded producer config: {producer_config}")

    if "healthcheck-consumer-config" in config:
        producer_config_dict = config["healthcheck-consumer-config"]
        kafka_consumer_config = KafkaConsumerConfig.parse_obj(producer_config_dict)
        topic_config_map: dict[str, list[PostgresqlProducerConfig]] = {}
        topics = []

        for topic in producer_config_dict["topics"]:
            topic_name = topic["source_topic"]
            config = PostgresqlProducerConfig.parse_obj(topic)

            if topic_name in topic_config_map:
                # we could have different postgresql writers for the same topic
                topic_config_map[topic_name].append(config)
            else:
                topic_config_map[topic_name] = [config]

            topics.append(topic_name)

        kafka_consumer_config.source_topics = topics
        consumer_config = ConsumerConfig(kafka_consumer_config, topic_config_map)
        logger.info(f"Loaded producer config: {consumer_config}")

    return ProgramConfig(general_config, consumer_config, producer_config)

import inspect
import os

from python_quickstart_repo.config.config import GeneralConfig
from python_quickstart_repo.config.kafka_consumer_config import KafkaConsumerConfig
from python_quickstart_repo.config.kafka_producer_config import KafkaProducerConfig
from python_quickstart_repo.config.page_fetcher_config import PageFetcherConfig
from python_quickstart_repo.config.postgresql_producer_config import (
    PostgresqlProducerConfig,
)
from python_quickstart_repo.config.yaml_config_reader import (
    ConsumerConfig,
    ProducerConfig,
    ProgramConfig,
    load_yaml_configs,
)


def test_load_program_config_with_env_variables():
    current_script_location = inspect.getframeinfo(inspect.currentframe()).filename
    current_dir = os.path.dirname(os.path.abspath(current_script_location))
    yaml_config = str(current_dir) + "/files/config_with_env.yaml"

    loaded_config = load_yaml_configs(yaml_config)

    general_config = GeneralConfig(debug=False)

    consumer_configs = ConsumerConfig(
        KafkaConsumerConfig(
            source_topics=["healthcheck-topic-cloud-providers"],
            bootstrap_servers=["localhost:9092"],
            group_id="healthcheck-cloud-group",
            auto_offset_reset="earliest",
        ),
        {
            "healthcheck-topic-cloud-providers": [
                PostgresqlProducerConfig(
                    connection_uri="postgresql://postgres:postgres@localhost:5432/postgres", table_name="default-table"
                )
            ]
        },
    )
    producer_configs = ProducerConfig(
        KafkaProducerConfig(bootstrap_servers=["localhost:9092"]),
        [
            PageFetcherConfig(
                destination_topic="default-topic",
                url="https://www.google.com",
                polling_interval_in_seconds=30,
                validated_regex=None,
            )
        ],
    )

    assert loaded_config == ProgramConfig(general_config, consumer_configs, producer_configs)

    os.environ["DEBUG"] = "true"
    os.environ["TABLE_NAME"] = "custom-table"
    os.environ["TOPIC"] = "custom-topic"

    general_config.debug = True
    producer_configs.page_fetcher_configs[0].destination_topic = "custom-topic"
    consumer_configs.topic_postgresql_config_dict["healthcheck-topic-cloud-providers"][0].table_name = "custom-table"

    loaded_config = load_yaml_configs(yaml_config)

    assert loaded_config == ProgramConfig(general_config, consumer_configs, producer_configs)

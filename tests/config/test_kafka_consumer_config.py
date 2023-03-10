import os

from python_quickstart_repo.config.kafka_consumer_config import KafkaConsumerConfig


def test_consumer_config_serde():
    os.environ["source_topics"] = "custom_topic"
    os.environ["bootstrap_servers"] = "127.0.0.1:9092,localhost:9092"
    os.environ["group_id"] = "group_id"
    os.environ["auto_offset_reset"] = "earliest"

    assert KafkaConsumerConfig().dict() == {
        "source_topics": ["custom_topic"],
        "bootstrap_servers": ["127.0.0.1:9092", "localhost:9092"],
        "group_id": "group_id",
        "ssl_security_protocol": None,
        "auto_offset_reset": "earliest",
    }

    expected_dict = {
        "source_topics": ["custom_topic"],
        "bootstrap_servers": ["url1", "url2"],
        "ssl_security_protocol": None,
        "group_id": "custom_group_id",
        "auto_offset_reset": "latest",
    }

    assert (
        KafkaConsumerConfig(
            source_topics=["custom_topic"],
            bootstrap_servers=["url1", "url2"],
            group_id="custom_group_id",
            auto_offset_reset="latest",
            ssl_security_protocol=None,
        ).dict()
        == expected_dict
    )

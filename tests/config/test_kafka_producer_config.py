import os

from python_quickstart_repo.config.kafka_producer_config import KafkaProducerConfig


def test_consumer_producer_serde():
    os.environ["destination_topic"] = "custom_topic"
    os.environ["bootstrap_servers"] = "127.0.0.1:9092,localhost:9092"
    assert KafkaProducerConfig().dict() == {
        "destination_topic": "custom_topic",
        "bootstrap_servers": ["127.0.0.1:9092", "localhost:9092"],
    }

    expected_dict = {"destination_topic": "destination_topic", "bootstrap_servers": []}

    assert KafkaProducerConfig(destination_topic="destination_topic", bootstrap_servers=[]).dict() == expected_dict
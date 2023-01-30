from typing import Any, Optional

from pydantic import BaseConfig, BaseSettings


class PostgresqlProducerConfig(BaseSettings):
    connection_uri: str
    table_name: str


class KafkaProducerConfig(BaseSettings):
    destination_topic: str
    bootstrap_servers: list[str]

    class Config(BaseConfig):
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "bootstrap_servers":
                return raw_val.split(",")
            return cls.json_loads(raw_val)


class KafkaConsumerConfig(BaseSettings):
    source_topic: str
    bootstrap_servers: list[str]
    group_id: str
    auto_offset_reset: str

    class Config(BaseConfig):
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "bootstrap_servers":
                return raw_val.split(",")
            return cls.json_loads(raw_val)

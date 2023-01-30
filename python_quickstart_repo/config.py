from typing import Any

from pydantic import BaseConfig, BaseSettings, constr

TableName = constr(regex="^[a-zA-Z_-]+$")


class PostgresqlProducerConfig(BaseSettings):
    connection_uri: str
    # the table name needs to be parsed or sanitized
    # because it is used in a SQL query and the asyncpg library does not sanitize it
    # more info here: https://github.com/MagicStack/asyncpg/issues/605
    table_name: TableName


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

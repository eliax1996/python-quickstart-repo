from typing import Any

from pydantic import BaseConfig, BaseSettings, Extra


class KafkaConsumerConfig(BaseSettings):
    source_topics: list[str] = []
    bootstrap_servers: list[str]
    group_id: str
    auto_offset_reset: str

    class Config(BaseConfig):
        extra = Extra.ignore

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "bootstrap_servers" or field_name == "source_topics":
                return raw_val.split(",")
            return cls.json_loads(raw_val)

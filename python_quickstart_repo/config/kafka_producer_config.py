from typing import Any

from pydantic import BaseConfig, BaseSettings, Extra


class KafkaProducerConfig(BaseSettings):
    bootstrap_servers: list[str]

    class Config(BaseConfig):
        extra = Extra.ignore

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "bootstrap_servers":
                return raw_val.split(",")
            return cls.json_loads(raw_val)
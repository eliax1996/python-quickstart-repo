from typing import Any, Optional

from pydantic import BaseConfig, BaseSettings, Extra

from python_quickstart_repo.config.sasl_security_protocol import SslSecurityProtocol


class KafkaConsumerConfig(BaseSettings):
    source_topics: list[str] = []
    ssl_security_protocol: Optional[SslSecurityProtocol] = None
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

from typing import Any, Optional

from pydantic import BaseConfig, BaseSettings, Extra

from python_quickstart_repo.config.sasl_security_protocol import SslSecurityProtocol


class KafkaProducerConfig(BaseSettings):
    bootstrap_servers: list[str]
    ssl_security_protocol: Optional[SslSecurityProtocol] = None

    class Config(BaseConfig):
        extra = Extra.ignore

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "bootstrap_servers":
                return raw_val.split(",")
            return cls.json_loads(raw_val)

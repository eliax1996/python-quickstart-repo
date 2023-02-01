import re
from typing import Optional

from pydantic import BaseConfig, BaseSettings, Extra


class PageFetcherConfig(BaseSettings):
    destination_topic: str
    url: str
    polling_interval_in_seconds: int
    validated_regex: Optional[re.Pattern] = None

    class Config(BaseConfig):
        extra = Extra.ignore

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Optional[re.Pattern]:
            if field_name in ["validated_regex", "regex"]:
                return re.compile(raw_val)
            return cls.json_loads(raw_val)

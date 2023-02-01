from typing import Optional

from pydantic import BaseConfig, BaseSettings, Extra


class PageFetcherConfig(BaseSettings):
    destination_topic: str
    url: str
    polling_interval_in_seconds: int
    regex: Optional[str]

    class Config(BaseConfig):
        extra = Extra.ignore

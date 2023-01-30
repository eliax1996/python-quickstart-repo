from typing import Any

from pydantic import BaseConfig, BaseSettings


class Config(BaseSettings):
    debug: bool

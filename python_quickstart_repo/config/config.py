from enum import Enum

from pyaml_env import BaseConfig
from pydantic import BaseSettings, Extra


class WorkingMode(Enum):
    """The working mode of the program."""
    PRODUCER = "HealthcheckProducer"
    CONSUMER = "HealthcheckConsumer"


class GeneralConfig(BaseSettings):
    debug: bool = False
    working_mode: WorkingMode = WorkingMode.PRODUCER

    class Config(BaseConfig):
        extra = Extra.ignore

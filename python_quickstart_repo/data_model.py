import json
from datetime import datetime, timedelta
from typing import Optional

from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder


@dataclass
class HealthCheckReply:
    status_code: int
    response_time: timedelta
    regex_match: Optional[bool]
    url: str
    measurement_time: datetime

    def __eq__(self, other):
        return (
            self.status_code == other.status_code
            and self.response_time.microseconds == other.response_time.microseconds
            and self.regex_match == other.regex_match
            and self.url == other.url
            and self.measurement_time.isoformat() == other.measurement_time.isoformat()
        )

    def __hash__(self):
        return hash(
            (
                self.status_code,
                self.response_time.microseconds,
                self.regex_match,
                self.url,
                self.measurement_time.isoformat(),
            )
        )

    def to_json(self) -> str:
        return json.dumps(self, default=pydantic_encoder)

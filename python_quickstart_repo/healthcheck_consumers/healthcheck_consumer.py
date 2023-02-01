from __future__ import annotations

from abc import abstractmethod
from typing import Generic, TypeVar

from python_quickstart_repo.http_checkers.page_fetcher import HealthCheckReply

T = TypeVar("T")


class HealthCheckConsumer(Generic[T]):
    """Abstract class representing the consumption of healthcheck messages.
    the return type T is meant to be treated as an acknowledgment message of type T."""

    @abstractmethod
    async def consume(self, healthcheck: HealthCheckReply) -> T:
        pass

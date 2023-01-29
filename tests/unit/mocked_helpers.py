import random
from datetime import datetime, timedelta
from typing import Callable

from python_quickstart_repo.health_reader import HealthCheckConsumer
from python_quickstart_repo.page_fetcher import AsyncFetcher, HealthCheckReply


class MockedAsyncFetcher(AsyncFetcher):
    def __init__(
        self,
        seed: int = 42,
        message_to_generate: int = 10,
        url: str = "https://www.myawesomedomain.com",
        datetime_function: Callable[[], datetime] = lambda: datetime.fromisocalendar(2021, 1, 1),
    ) -> None:
        random.seed(seed)
        self.reply_count = 0
        self.message_to_generate = message_to_generate
        self.reply_list = []
        for _ in range(0, message_to_generate):
            random_reply_delay = random.randint(20, 1200)
            random_status_code = random.choice([200, 500])
            random_match = random.choice([None, True, False])

            self.reply_list.append(
                HealthCheckReply(
                    status_code=random_status_code,
                    response_time=timedelta(milliseconds=random_reply_delay),
                    regex_match=random_match,
                    measurement_time=datetime_function(),
                    url=url,
                )
            )

    async def __anext__(self) -> HealthCheckReply:
        if self.reply_count == self.message_to_generate:
            raise StopAsyncIteration

        self.reply_count += 1
        index = self.reply_count - 1

        return self.reply_list[index]


class CollectorConsumer(HealthCheckConsumer[None]):
    def __init__(self) -> None:
        self.collected: list[HealthCheckReply] = []

    async def write(self, healthcheck: HealthCheckReply) -> None:
        self.collected.append(healthcheck)

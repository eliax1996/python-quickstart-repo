from __future__ import annotations

from hashlib import sha256
from types import TracebackType
from typing import AsyncContextManager, Type

import asyncpg

from python_quickstart_repo.config import PostgresqlProducerConfig
from python_quickstart_repo.data_model import HealthCheckReply
from python_quickstart_repo.health_reader import HealthCheckConsumer


class PostgresqlWriter(AsyncContextManager, HealthCheckConsumer[None]):
    def __init__(self, postgresql_config: PostgresqlProducerConfig) -> None:
        self.connection_uri = postgresql_config.connection_uri
        self.in_context = False

    async def __aenter__(self) -> PostgresqlWriter:
        self.in_context = True
        self.conn = await asyncpg.connect(self.connection_uri)
        await self._upsert_table()
        return self

    async def __aexit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        self.in_context = False
        await self.conn.close()
        return None

    async def write(self, healthcheck: HealthCheckReply) -> None:
        assert self.in_context
        await self._upsert_measure(healthcheck)

    async def _upsert_measure(self, healthcheck: HealthCheckReply) -> None:
        assert self.in_context
        await self.conn.execute(
            """INSERT INTO healthcheck_measurements (
                   url_digest,
                   measurement_time,
                   response_time_microseconds,
                   uri,
                   status_code,
                   regex_present,
                   regex_match
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (url_digest, measurement_time) DO UPDATE SET
                uri = EXCLUDED.uri,
                response_time_microseconds = EXCLUDED.response_time_microseconds,
                status_code = EXCLUDED.status_code,
                regex_present = EXCLUDED.regex_present,
                regex_match = EXCLUDED.regex_match
            """,
            sha256(healthcheck.url.encode("utf-8")).hexdigest(),
            healthcheck.measurement_time,
            healthcheck.response_time.microseconds,
            healthcheck.url,
            healthcheck.status_code,
            healthcheck.regex_match is not None,
            healthcheck.regex_match,
        )

    async def _upsert_table(self) -> None:
        assert self.in_context
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS healthcheck_measurements (
                   url_digest CHAR(256),
                   measurement_time TIMESTAMP,
                   response_time_microseconds BIGINT NOT NULL,
                   uri text NOT NULL,
                   status_code int NOT NULL,
                   regex_present bool NOT NULL,
                   regex_match bool,
                   PRIMARY KEY (url_digest, measurement_time)
            );"""
        )

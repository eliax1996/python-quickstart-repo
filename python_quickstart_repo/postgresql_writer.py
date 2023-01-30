from __future__ import annotations

from hashlib import sha256
from types import TracebackType
from typing import AsyncContextManager, Type

import asyncpg
from asyncpg import Connection

from python_quickstart_repo.config import PostgresqlProducerConfig
from python_quickstart_repo.data_model import HealthCheckReply
from python_quickstart_repo.health_reader import HealthCheckConsumer


class HealthCheckPostgresqlWriter(HealthCheckConsumer[None]):
    def __init__(
            self,
            connection: Connection,
            postgresql_config: PostgresqlProducerConfig
    ) -> None:
        self.conn = connection
        self.postgresql_config = postgresql_config

    async def write(self, healthcheck: HealthCheckReply) -> None:
        await self._upsert_measure(healthcheck)

    async def _upsert_measure(self, healthcheck: HealthCheckReply) -> None:
        await self.conn.execute(
            f"""INSERT INTO ${self.postgresql_config.table_name} (
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


class PostgresqlWriter(AsyncContextManager):
    def __init__(self, postgresql_config: PostgresqlProducerConfig) -> None:
        self.postgresql_config = postgresql_config

    async def __aenter__(self) -> HealthCheckPostgresqlWriter:
        self.conn: Connection = await asyncpg.connect(self.postgresql_config.connection_uri)
        await self._upsert_table()
        return HealthCheckPostgresqlWriter(self.conn, self.postgresql_config)

    async def __aexit__(
            self,
            __exc_type: Type[BaseException] | None,
            __exc_value: BaseException | None,
            __traceback: TracebackType | None,
    ) -> bool | None:
        await self.conn.close()
        return None

    async def _upsert_table(self) -> None:
        await self.conn.execute(
            f"""CREATE TABLE IF NOT EXISTS ${self.postgresql_config.table_name} (
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

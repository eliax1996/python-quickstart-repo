from typing import Type

from pydantic import BaseSettings, constr, AnyUrl

TableName: Type[str] = constr(regex="^[a-zA-Z_-]+$")


class PostgresqlProducerConfig(BaseSettings):
    connection_uri: AnyUrl

    # the table name needs to be parsed or sanitized
    # because it is used in a SQL query and the asyncpg library does not sanitize it
    # more info here: https://github.com/MagicStack/asyncpg/issues/605

    # also, mypy is broken against the constr regex checks.
    # See: https://github.com/pydantic/pydantic/issues/156
    table_name: TableName  # type: ignore

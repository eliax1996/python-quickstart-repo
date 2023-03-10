FROM python:3.10-slim-bullseye AS builder

ENV POETRY_HOME "/opt/poetry"
ENV POETRY_VIRTUALENVS_IN_PROJECT 1
ENV POETRY_VIRTUALENVS_CREATE 1
ENV POETRY_NO_INTERACTION 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR off
ENV PATH "$POETRY_HOME/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y curl && curl -sSL https://install.python-poetry.org | python3 -

RUN poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock /app/

RUN poetry install --no-ansi --without dev

FROM python:3.10-slim-bullseye AS runtime

WORKDIR /app

COPY python_quickstart_repo /app/python_quickstart_repo
COPY main.py /app/
COPY --from=builder /app /app

ENTRYPOINT ["./.venv/bin/python", "main.py"]
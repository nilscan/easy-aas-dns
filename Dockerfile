FROM python:3.9-slim

ENV PYTHONPATH=/app

RUN pip install poetry

WORKDIR /app

ADD poetry.lock poetry.toml pyproject.toml /app
RUN poetry install

ADD ./controllers bin /app

ENTRYPOINT /app/bin/run_controllers.sh

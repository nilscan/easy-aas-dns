FROM python:3.9-slim

ENV PYTHONPATH=/app

RUN pip install poetry

WORKDIR /app

ADD poetry.lock poetry.toml pyproject.toml /app
RUN poetry install

ADD ./controllers /app/controllers
ADD ./bin /app/bin

RUN  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

ENTRYPOINT /app/bin/run_controllers.sh

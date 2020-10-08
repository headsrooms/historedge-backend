FROM python:3.9-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=off

USER root

COPY . /app
WORKDIR /app

RUN apt-get -y update && apt-get -y upgrade && apt-get -y -qq install curl build-essential git
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/usr/local/poetry python
RUN /usr/local/poetry/bin/poetry install --no-dev --no-interaction --no-ansi
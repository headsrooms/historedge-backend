# Historedge

Historedge is a personal Google or a [Memex](https://es.wikipedia.org/wiki/Memex) of your browser history.

## Install

    pip install poetry
    poetry install

## Run

Firstly, rename the file `sample.env` to `.env` and fill with values if needed.

To run the server execute:

    poetry run uvicorn api.app:app --port 80 --env-file .env

## Test

    poetry run pytest

## Docker

To run with docker execute:

    docker-compose build
    docker-compose up

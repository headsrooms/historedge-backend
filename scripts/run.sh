#!/bin/sh -e

if [ -d "venv" ]; then
  BIN_PATH="venv/bin/"
else
  BIN_PATH=""
fi

if [ ! $PORT ]; then
  PORT=5000
fi

set -x
poetry run uvicorn api.app:app --port $PORT --host 0.0.0.0 --env-file .env ${@}

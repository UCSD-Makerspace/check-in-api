#!/bin/bash
set -a
source "$(dirname "$0")/.env"
set +a

exec "$(dirname "$0")/.venv/bin/uvicorn" app:app --app-dir src --reload

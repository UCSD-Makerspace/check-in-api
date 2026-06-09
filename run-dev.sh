#!/bin/bash
set -a
source "$(dirname "$0")/.env"
set +a

#DEV_MODE=true exec "$(dirname "$0")/.venv/bin/uvicorn" app:app --app-dir src --reload
exec "$(dirname "$0")/.venv/bin/uvicorn" app:app --app-dir src --reload

from __future__ import annotations

import logging
import os
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from services import cache
from services.ucsd import ExternalApiError
from routes import check_in, accounts, traffic_light

logging.basicConfig(level=logging.INFO)

DEV_MODE = os.environ.get("DEV_MODE", "").lower() == "true"

SILENT_PATHS = frozenset(["/health", "/traffic-light"])


class _SilentPathFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(f" {path} " in msg or f'"{path} ' in msg for path in SILENT_PATHS)


logging.getLogger("uvicorn.access").addFilter(_SilentPathFilter())


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    if DEV_MODE:
        logging.warning("=" * 60)
        logging.warning("  DEV MODE — UCSD and Fabman APIs returning dummy data")
        logging.warning("=" * 60)
    cache.start()
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(ExternalApiError)
async def external_api_error_handler(request: Request, exc: ExternalApiError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"api": exc.api})


@app.middleware("http")
async def log_timing(request: Request, call_next: RequestResponseEndpoint) -> Response:
    start = time.time()
    response = await call_next(request)
    ms = (time.time() - start) * 1000
    if request.url.path not in SILENT_PATHS:
        logging.info(f"[{request.method}] {request.url.path} {response.status_code} {ms:.0f}ms")
    return response


app.include_router(check_in.router)
app.include_router(accounts.router)
app.include_router(traffic_light.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

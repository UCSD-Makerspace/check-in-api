import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request

from services import cache
from routes import check_in, accounts

logging.basicConfig(level=logging.INFO)

DEV_MODE = os.environ.get("DEV_MODE", "").lower() == "true"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if DEV_MODE:
        logging.warning("=" * 60)
        logging.warning("  DEV MODE — UCSD and Fabman APIs returning dummy data")
        logging.warning("=" * 60)
    cache.start()
    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_timing(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    ms = (time.time() - start) * 1000
    logging.info(f"[{request.method}] {request.url.path} {response.status_code} {ms:.0f}ms")
    return response


app.include_router(check_in.router)
app.include_router(accounts.router)


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

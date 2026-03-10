import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
import ucsd_api
import fabman
import sheets

logging.basicConfig(level=logging.INFO)

# TODO: the entire api should be rewritten to be in one place with the controllers in another place


@asynccontextmanager
async def lifespan(_app: FastAPI):
    sheets.start_cache()
    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_timing(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    ms = (time.time() - start) * 1000
    logging.info(f"[{request.method}] {request.url.path} {response.status_code} {ms:.0f}ms")
    return response


app.include_router(ucsd_api.router)
app.include_router(fabman.router)
app.include_router(sheets.router)


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

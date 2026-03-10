import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
import ucsd_api
import fabman
import sheets

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    sheets.start_cache()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(ucsd_api.router)
app.include_router(fabman.router)
app.include_router(sheets.router)


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

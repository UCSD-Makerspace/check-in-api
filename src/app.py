from datetime import datetime

from fastapi import FastAPI

from . import ucsd_api, fabman, sheets

app = FastAPI()
app.include_router(ucsd_api.router)
app.include_router(fabman.router)
app.include_router(sheets.router)


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

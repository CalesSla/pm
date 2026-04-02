import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="PM App", lifespan=lifespan)
app.include_router(api_router)

STATIC_DIR = Path(os.environ.get("STATIC_DIR", "static"))


@app.get("/")
def index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file, media_type="text/html")
    return HTMLResponse("<h1>Frontend not built yet</h1>", status_code=200)


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")

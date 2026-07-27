import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request

from app.db import init_db
from app.logging import configure_logging
from app.routers import chat, demo, health, jobs, resumes

configure_logging()
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    log.info("startup", db="ready")
    yield


app = FastAPI(title="Rumbo API", lifespan=lifespan)


@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    log.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round((time.perf_counter() - start) * 1000, 1),
    )
    return response


app.include_router(health.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(demo.router)
app.include_router(chat.router)

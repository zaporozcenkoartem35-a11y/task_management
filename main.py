import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import routers_api
from app.core.middlewares import logger_middleware





app = FastAPI(title="Task Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(logger_middleware)

app.include_router(routers_api.api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    await asyncio.sleep(0.51)
    return {"status": "ok"}

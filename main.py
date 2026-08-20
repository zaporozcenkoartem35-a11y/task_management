from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import routers_api

app = FastAPI(
    title="Task Management API",
    version="1.0.0",
    description="REST API for Task Management System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routers_api.api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}

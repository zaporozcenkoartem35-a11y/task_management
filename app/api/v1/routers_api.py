from fastapi import APIRouter
from app.api.v1 import comments_api, tasks_api, users_api

api_router = APIRouter()
api_router.include_router(users_api.router, prefix="/auth", tags=["Auth"])
api_router.include_router(tasks_api.router, tags=["Tasks"])
api_router.include_router(comments_api.router, tags=["Comments"])

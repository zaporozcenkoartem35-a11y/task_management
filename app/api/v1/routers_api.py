from fastapi import APIRouter
from app.api.v1 import users_api

api_router = APIRouter()
api_router.include_router(users_api.router, prefix="/auth", tags=["Auth"])



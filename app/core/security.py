


from datetime import datetime, timedelta, timezone
import os

import jwt
from pwdlib import PasswordHash
from app.core.config import settings

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


async def create_access_token(user_data: dict):
    to_encode = user_data.copy()
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode['exp'] = expire_time
    to_encode['type'] = 'access'

    token = jwt.encode(payload=to_encode, key=settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


async def create_refresh_token(user_data: dict):
    to_encode = user_data.copy()
    expire_time = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode['exp'] = expire_time
    to_encode['type'] = 'refresh'

    token = jwt.encode(payload=to_encode, key=settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


async def decode_token(token: str):
    return jwt.decode(token, settings.SECRET_KEY, [settings.ALGORITHM])

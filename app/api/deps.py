from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import async_session_maker
from app.models.user_mod import UserRole
from app.schemas.user_pydan import UserJWTData
from app.core.redis import redis_client

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def decode_token(token: str = Depends(oauth2_scheme)):
    try:
        return jwt.decode(token, settings.SECRET_KEY, [settings.ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


class JWTChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        self._allowed_roles = allowed_roles

    def __call__(self, jwt_data: dict = Depends(decode_token)):
        if jwt_data.get('type') != 'access':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Access token required',
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if jwt_data.get('role') not in self._allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail='Access forbidden: insufficient permissions'
            )

        return UserJWTData(
            id=int(jwt_data['sub']),
            role=jwt_data['role']
        )


allowed_client = JWTChecker([UserRole.USER])
allowed_admin = JWTChecker([UserRole.ADMIN])
allowed_all = JWTChecker([UserRole.USER, UserRole.ADMIN])


async def check_comment_rate_limit(user_data: UserJWTData = Depends(allowed_client)):
    key = f"rate_limit:comments:{user_data.id}"

    count = await redis_client.incr(key)

    if count == 1:
        await redis_client.expire(key, 60)

    if count > 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many comments. Limit is 5 comments per minute."
        )
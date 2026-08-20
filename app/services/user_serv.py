from datetime import datetime, timezone

from fastapi.security import OAuth2PasswordRequestForm
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from app.crud.user_crud import add_user_in_db, check_user_in_db
from app.models.user_mod import UserTable
from app.schemas.user_pydan import LoginResponse, UserCreateModel, UserDBResponse
from app.core.exceptions import UserCreateError, NoUserError


async def prepare_to_create_user(user_data: UserCreateModel,
                                 session: AsyncSession):

    check_user: UserTable = await check_user_in_db(username=user_data.username,
                                                   session=session)
    if check_user:
        raise UserCreateError
    
    hashed_password: str = get_password_hash(password=user_data.password)
    cur_user: UserTable = await add_user_in_db(user_data=UserTable(username=user_data.username,
                                                                   hashed_password=hashed_password,
                                                                   created_at=datetime.now(timezone.utc)),
                                                session=session)

    return UserDBResponse.model_validate(cur_user)


async def prepare_to_login_user(user_data: OAuth2PasswordRequestForm,
                                session: AsyncSession):
    cur_user: UserTable = await check_user_in_db(username=user_data.username,
                                                 session=session)
    if not cur_user:
        raise NoUserError

    if not verify_password(user_data.password, cur_user.hashed_password):
        raise NoUserError

    access_token = await create_access_token(user_data={'sub': str(cur_user.id),
                                                        'role': str(cur_user.role)})
    refresh_token = await create_refresh_token(user_data={'sub': str(cur_user.id),
                                                          'role': str(cur_user.role)})

    return LoginResponse(access_token=access_token,
                         refresh_token=refresh_token)


async def prepare_to_change_refresh_token(refresh_token: str):
    try:
        decode_data: dict = await decode_token(token=refresh_token)

        if decode_data['type'] != 'refresh':
            raise jwt.PyJWTError

        new_access_token = await create_access_token(user_data={'sub': str(decode_data['sub']),
                                                                'role': str(decode_data['role'])})
        return new_access_token
    except jwt.PyJWTError:
        raise jwt.PyJWTError

    

    



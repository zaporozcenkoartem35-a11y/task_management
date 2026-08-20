from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_session
from app.core.exceptions import NoUserError, UserCreateError
from app.schemas.user_pydan import LoginResponse, UserCreateModel, UserDBResponse
from app.services.user_serv import prepare_to_change_refresh_token, prepare_to_create_user, prepare_to_login_user


router = APIRouter()


@router.post('/register', response_model=UserDBResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreateModel,
                      session: AsyncSession = Depends(get_session)):
    try:
        cur_user: UserDBResponse = await prepare_to_create_user(user_data=user_data,
                                                     session=session)
    except UserCreateError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Username already taken')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')
    return cur_user


@router.post('/login', response_model=LoginResponse)
async def login_user(user_data: OAuth2PasswordRequestForm = Depends(), 
                     session: AsyncSession = Depends(get_session)):
    try:
        response_data: LoginResponse = await prepare_to_login_user(user_data=user_data,
                                                                   session=session)
    except NoUserError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid username or password')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')

    return response_data


@router.post('/refresh')
async def check_refresh_token(refresh_token: str = Body(embed=True)):
    try:
        new_access_token: str = await prepare_to_change_refresh_token(refresh_token=refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired refresh token')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')
    

    return {'access_token': new_access_token,
            'token_type': 'bearer'}

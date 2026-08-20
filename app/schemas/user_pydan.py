

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class UserCreateModel(BaseModel):
    username: str
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not 8 <= len(value) <= 15:
            raise ValueError("Password must be 8-15 characters long")
        
        if not any(item.isdigit() for item in value):
            raise ValueError("Password must contain at least one number")

        return value
        


class UserDBResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class UserJWTData(BaseModel):
    id: int
    role: str
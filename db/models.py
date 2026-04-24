from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    Hash_password: str
    created_at: datetime


class UserUpdateEmail(BaseModel):
    email: EmailStr
    Hash_password: str
    updated_at: datetime


class UserDelete(BaseModel):
    email: EmailStr
    deleted_at: datetime


class UserInDB(BaseModel):
    email: EmailStr
    Hash_password: str
    created_at: datetime
    role: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime
    role: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenResponseONLogin(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str

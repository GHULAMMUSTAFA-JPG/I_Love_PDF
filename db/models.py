from datetime import datetime

from pydantic import BaseModel, EmailStr

# User Models


class UserCreate(BaseModel):
    email: EmailStr
    Hash_password: str
    created_at: datetime


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


class UserUpdateEmail(BaseModel):
    email: EmailStr
    Hash_password: str
    updated_at: datetime


class UserDelete(BaseModel):
    email: EmailStr
    deleted_at: datetime


# Token Models


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

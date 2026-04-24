import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)


def create_access_token(dict: dict):
    to_encode = dict.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is missing in environment variables")
    return jwt.encode(to_encode, SECRET_KEY, ALGORITHM)


def decode_token(token: str):
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is missing in environment variables")
    token_data = jwt.decode(token, SECRET_KEY, ALGORITHM)
    return token_data


def create_refresh_token(dict: dict):
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = secrets.token_urlsafe(32)
    to_encode = dict.copy()
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is missing in environment variables")
    refresh = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return refresh, jti, expire


async def save_refresh_token(
    db: AsyncIOMotorDatabase, jti: str, user_id: str, expires_at: datetime
):
    await db["refresh_tokens"].insert_one(
        {
            "jti": jti,
            "expires_at": expires_at,
            "user_id": user_id,
            "revoke": False,
            "created_at": datetime.now(timezone.utc),
        }
    )


async def is_refresh_token_valid(jti: str, db: AsyncIOMotorDatabase):
    token = await db["refresh_tokens"].find_one({"jti": jti})
    if not token:
        return False
    if token["revoke"]:
        return False
    return True


async def revoke_refresh_token(jti: str, db: AsyncIOMotorDatabase):
    await db["refresh_tokens"].update_one({"jti": jti}, {"$set": {"revoke": True}})


async def revoke_all_refresh_token(user_id: str, db: AsyncIOMotorDatabase):
    await db["refresh_tokens"].delete_many(
        {"user_id": user_id}, {"$set": {"revoked": True}}
    )

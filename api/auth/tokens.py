from datetime import datetime, timedelta
from time import timezone

from jwt import decode, encode

from core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY


def create_token(dict: dict):
    to_encode = dict.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    pass


def create_refresh_token(dict: dict):
    pass


def save_refresh_token(token: str, user_id: int):
    pass


def refresh_access_token(refresh_token: str):
    pass


def revoke_refresh_token(refresh_token: str):
    pass


def revoke_all_access_token(access_token: str):
    pass

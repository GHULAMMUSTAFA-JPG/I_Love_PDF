from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError

from api.auth.hashing import hash_password, verify_password
from api.auth.tokens import (
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_refresh_token,
    save_refresh_token,
)
from api.dependencies.auth_dependencies import UserExists
from db.models import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserInDB,
    UserOut,
)
from db.repositories import get_db

app = APIRouter()


@app.post("/health")
async def health():
    return {"message": "You called the right service"}


@app.post("/signup", response_model=UserOut, status_code=201)
async def signup(request: UserCreate, db=Depends(get_db)):

    if await UserExists(request.email, db):
        return {"message": "User already exists"}

    user_in_db = UserInDB(
        email=request.email,
        Hash_password=hash_password(request.Hash_password),
        created_at=datetime.now(timezone.utc),
        role="user",
    )

    result = await db("user").insert_one(user_in_db.model_dump())

    return UserOut(
        id=str(result.inserted_id),
        email=request.email,
        created_at=user_in_db.created_at,
        role=user_in_db.role,
    )


@app.post("/login", response_model=TokenResponse, status_code=201)
async def login(request: LoginRequest, db=Depends(get_db)):

    if await UserExists(request.email, db):
        user = await db["users"].find_one({"email": request.email})
        if verify_password(request.password, user["Hash_password"]):
            # Make JWT token here
            user_id = str(user["_id"])
            access_token = create_access_token({"sub": user_id, "role": "user"})
            refresh, jti, expires_at = create_refresh_token({"sub": user_id})
            await save_refresh_token(db, jti, user_id, expires_at)
            #  write code to return JWT token
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh,
            )
        return {"message": "Invalid credentials"}
    return {"message": "User not found"}


@app.post("/refresh", response_model=AccessTokenResponse)
async def refresh(payload: RefreshRequest, db=Depends(get_db)):
    invalid = HTTPException(401, "Invalid refresh token")
    try:
        data = decode_token(payload.refresh_token)
    except JWTError:
        raise invalid
    user_id = data["sub"]
    access_token = create_access_token({"sub": user_id, "role": "user"})
    return AccessTokenResponse(
        access_token=access_token,
    )


@app.post("/logout", status_code=200)
async def logout(payload: RefreshRequest, db=Depends(get_db)):
    invalid = HTTPException(401, "Invalid refresh token")
    try:
        data = decode_token(payload.refresh_token)
        jti = data["jti"]
        await revoke_refresh_token(jti, db)
        return {"message": "Logged out successfully"}
    except JWTError:
        raise invalid

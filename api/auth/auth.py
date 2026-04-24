from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from api.auth.hashing import hash_password, verify_password
from api.dependencies.auth_dependencies import UserExists
from db.models import LoginRequest, TokenResponse, UserCreate, UserInDB, UserOut
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
    )

    result = await db("user").insert_one(user_in_db.model_dump())

    return UserOut(
        id=str(result.inserted_id),
        email=request.email,
        created_at=user_in_db.created_at,
    )


@app.post("/login", response_model=TokenResponse, status_code=201)
async def login(request: LoginRequest, db=Depends(get_db)):

    if await UserExists(request.email, db):
        user = await db["users"].find_one({"email": request.email})
        if verify_password(request.password, user["Hash_password"]):
            # Make JWT token here

            #  write code to return JWT token
            return TokenResponse(
                access_token="",
                token_type="bearer",
            )
        return {"message": "Invalid credentials"}
    return {"message": "User not found"}

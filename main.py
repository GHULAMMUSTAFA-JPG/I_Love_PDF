from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from api.auth.auth import app as auth_router

mongo_url = "mongodb://localhost:27017"
db_name = "orc"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_client = AsyncIOMotorClient(mongo_url)
    app.state.db = app.state.mongo_client[db_name]
    await app.state.db["ocr"].create_index("email", unique=True)
    yield
    app.state.mongo_client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "You called the right service"}

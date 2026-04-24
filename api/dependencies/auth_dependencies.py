from motor.motor_asyncio import AsyncIOMotorDatabase


async def UserExists(email: str, db: AsyncIOMotorDatabase):

    user = await db["users"].find_one({"email": email})

    return user is not None

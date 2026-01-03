from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None

    def connect(self):
        self.client = AsyncIOMotorClient(
            host=settings.MONGO_HOST,
            port=settings.MONGO_PORT,
            username=settings.MONGO_USER,
            password=settings.MONGO_PASS
        )
        print("Connected to MongoDB")

    def close(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")
    
    def get_db(self):
        return self.client[settings.MONGO_DB_NAME]

db = Database()

async def get_database():
    return db.get_db()

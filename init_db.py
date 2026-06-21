import asyncio
import logging
from app.database import engine
from app.database.models import Base

logging.basicConfig(level=logging.INFO)

async def create_tables():
    print("PostgreSQL jadvallarini yaratish boshlandi...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Barcha jadvallar (users, listings, photos) muvaffaqiyatli yaratildi!")

if __name__ == "__main__":
    asyncio.run(create_tables())
  

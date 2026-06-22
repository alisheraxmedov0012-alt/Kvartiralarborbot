import asyncio
import logging
import sys
import os

# Loyiha yo'llarini to'g'ri sozlash
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.database.models import Base  # Modellaringiz turgan asosiy Base

logging.basicConfig(level=logging.INFO)

async def create_tables():
    print("PostgreSQL jadvallarini tekshirish va yaratish boshlandi...")
    try:
        async with engine.begin() as conn:
            # Base ga bog'langan barcha modellarni (users, listings...) yaratadi
            await conn.run_sync(Base.metadata.create_all)
        print("Muvaffaqiyatli: Barcha jadvallar bazada qurildi!")
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    asyncio.run(create_tables())
    

import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database.models import Base

# 1. DATABASE_URL manzilini Railway o'zgaruvchilaridan o'qish
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# 2. Asenkron Engine va Session yaratish
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 3. MAJBURIY SINXRON JADVAL YARATISH (Poygada g'olib bo'lish uchun)
if DATABASE_URL:
    try:
        sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        sync_engine = create_engine(sync_url)
        # Barcha jadvallarni (users, listings...) srazu yaratadi
        Base.metadata.create_all(sync_engine)
        print("Baza jadvallari birinchi soniyadanoq muvaffaqiyatli qurildi!")
    except Exception as e:
        print(f"Sinxron yaratishda xatolik: {e}")

async def get_db():
    async with async_session() as session:
        yield session
        

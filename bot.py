oʻimport asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from sqlalchemy import create_engine

# 1. Base va modellarni xotiraga majburiy yuklash
try:
    from app.database.models import Base, User, Listing, Photo, AdminSetting
except ImportError:
    try:
        from app.database import Base
        User = Listing = Photo = AdminSetting = None
    except ImportError:
        from app.models import Base
        User = Listing = Photo = AdminSetting = None

from app.config import settings
from app.handlers import start, listing, admin, profile
from app.middlewares.antispam import AntiSpamMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 2. XAVFSIZLIK MEXANIZMI: Bot elementlari yuklanishidan oldin jadvallarni sinxron qurish
database_url = os.environ.get("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)
if database_url:
    # Agar asenkron havola bo'lsa, sinxron yaratish uchun to'g'rilaymiz
    if "postgresql+asyncpg://" in database_url:
        sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    else:
        sync_url = database_url if database_url.startswith("postgresql://") else None
    
    if sync_url:
        try:
            # Hech qanday asenkron to'siqsiz, to'g'ridan-to'g'ri bazada jadvallarni quradi
            sync_engine = create_engine(sync_url)
            Base.metadata.create_all(sync_engine)
            logging.info("Sinxron tekshiruv: Barcha jadvallar (users, listings...) bazada tayyor!")
        except Exception as e:
            logging.error(f"Sinxron jadvallarni yaratishda xato (Bot baribir ishga tushadi): {e}")

async def main():
    # DATABASE_URL ni asenkron engine uchun sozlash
    async_url = os.environ.get("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)
    if async_url and async_url.startswith("postgresql://"):
        async_url = async_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # 3. Redis ulanishi
    redis_password = os.environ.get("REDIS_PASSWORD") or os.environ.get("REDISPASSWORD") or getattr(settings, "REDIS_PASSWORD", None)
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=redis_password if redis_password else None,
        decode_responses=True
    )
    storage = RedisStorage(redis)

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    # Middleware va Routerlarni ulash
    dp.message.middleware(AntiSpamMiddleware(redis=redis, limit=2))

    dp["redis"] = redis
    
    dp.include_router(start.router)
    dp.include_router(listing.router)
    dp.include_router(admin.router)
    dp.include_router(profile.router)

    logging.info("Bot muvaffaqiyatli ishga tushdi!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await redis.close()

if __name__ == "__main__":
    asyncio.run(main())
    

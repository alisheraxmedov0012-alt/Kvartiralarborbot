import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from sqlalchemy import create_engine

# 1. Base va modellarni xotiraga yuklash
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 2. XAVFSIZLIK MEXANIZMI: Jadvallarni tekshirish
database_url = os.environ.get("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)
if database_url:
    if "postgresql+asyncpg://" in database_url:
        sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    else:
        sync_url = database_url if database_url.startswith("postgresql://") else None
        
    if sync_url:
        try:
            sync_engine = create_engine(sync_url)
            Base.metadata.create_all(sync_engine)
            logging.info("Sinxron tekshiruv muvaffaqiyatli.")
        except Exception as e:
            logging.error(f"Jadvallarda xato: {e}")

async def main():
    # Redis ulanishi
    redis_password = os.environ.get("REDIS_PASSWORD") or os.environ.get("REDISPASSWORD")
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=redis_password if redis_password else None,
        decode_responses=True
    )
    storage = RedisStorage(redis)

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    # 3. ANTISPANNI ERRORSIZ, XAVFSIZ ULASH
    try:
        from app.middlewares.antispan import AntiSpanMiddleware
        dp.message.middleware(AntiSpanMiddleware(redis=redis, limit=2))
        dp.callback_query.middleware(AntiSpanMiddleware(redis=redis, limit=2))
        logging.info("AntiSpanMiddleware muvaffaqiyatli ulandi.")
    except ImportError:
        try:
            from app.middleware.antispan import AntiSpanMiddleware
            dp.message.middleware(AntiSpanMiddleware(redis=redis, limit=2))
            dp.callback_query.middleware(AntiSpanMiddleware(redis=redis, limit=2))
            logging.info("AntiSpanMiddleware (singular path) ulandi.")
        except ImportError:
            logging.warning("⚠️ Antispan fayli topilmadi! Bot antispan-siz xavfsiz rejimda ishlamoqda.")

    # Routerlarni ulash
    dp.include_router(start.router)
    dp.include_router(listing.router)
    dp.include_router(admin.router)
    dp.include_router(profile.router)

    logging.info("Bot muvaffaqiyatli ishga tushdi!")

    try:
        await dp.start_polling(bot, redis=redis)
    finally:
        await bot.session.close()
        await redis.close()

if __name__ == "__main__":
    asyncio.run(main())
    

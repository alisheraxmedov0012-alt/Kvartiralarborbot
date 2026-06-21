import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

# Engine va Base importini xavfsiz (try-except) blokda qilamiz
engine = None
Base = None

try:
    from app.database import engine as eng
    engine = eng
except ImportError:
    try:
        from app.database.connection import engine as eng
        engine = eng
    except ImportError:
        try:
            from app.db import engine as eng
            engine = eng
        except ImportError:
            pass

try:
    from app.database.models import Base as b_obj
    Base = b_obj
except ImportError:
    try:
        from app.database import Base as b_obj
        Base = b_obj
    except ImportError:
        pass

from app.config import settings
from app.handlers import start, listing, admin, profile
from app.middlewares.antispam import AntiSpamMiddleware

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    # 1. PostgreSQL jadvallarini xavfsiz tekshirish va yaratish
    if engine and Base:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logging.info("Barcha baza jadvallari muvaffaqiyatli tekshirildi.")
        except Exception as e:
            logging.error(f"Jadvallarni yaratishda xato yuz berdi: {e}")
    else:
        logging.warning("DATABASE ENGINE yoki BASE topilmadi, jadvallar avtomatik yaratilmadi.")

    # 2. Redis ulanishi (OS darajasida xavfsiz o'qish)
    redis_password = os.environ.get("REDIS_PASSWORD") or os.environ.get("REDISPASSWORD") or getattr(settings, "REDIS_PASSWORD", None)

    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=redis_password if redis_password else None,
        decode_responses=True
    )
    
    storage = RedisStorage(redis)

    # Bot va Dispatcher obyektlari
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    # Global Middlewarelarni ulash
    dp.message.middleware(AntiSpamMiddleware(redis=redis, limit=2))

    # Routerlarni ulash
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
    

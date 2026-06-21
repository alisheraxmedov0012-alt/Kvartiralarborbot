import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

# PostgreSQL uchun kerakli narsalarni yuklaymiz
try:
    from app.database import engine, Base 
except ImportError:
    try:
        from app.db import engine, Base
    except ImportError:
        engine, Base = None, None

from app.config import settings
from app.handlers import start, listing, admin, profile
from app.middlewares.antispam import AntiSpamMiddleware

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    # 1. SQL jadvalini majburiy ravishda xom SQL buyrug'i bilan yaratish
    if engine:
        try:
            from sqlalchemy import text
            async with engine.begin() as conn:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        telegram_id BIGINT UNIQUE NOT NULL,
                        username VARCHAR(255),
                        full_name VARCHAR(255),
                        phone VARCHAR(50),
                        referrer_id BIGINT,
                        is_premium BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
            logging.info("PostgreSQL 'users' jadvali majburan tekshirildi/yaratildi!")
        except Exception as e:
            logging.error(f"Jadval yaratishda SQL xatosi: {e}")

    # 2. Redis ulanishi (OS darajasida xavfsiz va dinamik o'qish)
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

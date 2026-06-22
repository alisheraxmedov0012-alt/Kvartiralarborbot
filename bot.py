import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

# SQLAlchemy uchun kerakli modullarni yuklaymiz
from sqlalchemy.ext.asyncio import create_async_engine

# Faqat modellarni ifodalovchi Base'ni import qilamiz
try:
    from app.database.models import Base
except ImportError:
    try:
        from app.database import Base
    except ImportError:
        from app.models import Base

from app.config import settings
from app.handlers import start, listing, admin, profile
from app.middlewares.antispam import AntiSpamMiddleware

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    # 1. DATABASE_URL manzilini Railway o'zgaruvchilaridan majburiy o'qish
    database_url = os.environ.get("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)
    
    # Agar manzil 'postgresql://' bilan boshlansa, uni asenkron 'postgresql+asyncpg://' ga o'giramiz
    if database_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # 2. Engine obyektini to'g'ridan-to'g'ri shu yerda yaratamiz va jadvallarni quramiz
    if database_url:
        try:
            engine = create_async_engine(database_url, echo=False)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logging.info("PostgreSQL jadvallari (users, listings...) muvaffaqiyatli tekshirildi/yaratildi!")
        except Exception as e:
            logging.error(f"Ma'lumotlar bazasi jadvallarini yaratishda xato: {e}")
    else:
        logging.error("DATABASE_URL topilmadi! PostgreSQL ulana olmadi.")

    # 3. Redis ulanishi (OS darajasida xavfsiz o'qish)
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
    

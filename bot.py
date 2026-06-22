import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine

# 1. Base va barcha modellarni majburan xotiraga yuklaymiz (Shunda SQLAlchemy jadvallarni aniq yaratadi)
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

async def main():
    # 2. DATABASE_URL ni o'qish va asenkron formatga o'tkazish
    database_url = os.environ.get("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)
    if database_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # 3. Jadvallarni majburiy ravishda yaratish
    if database_url:
        try:
            engine = create_async_engine(database_url, echo=False)
            async with engine.begin() as conn:
                # Modellarni aniq ko'rgani uchun endi 'users', 'listings' hammasini ochadi
                await conn.run_sync(Base.metadata.create_all)
            logging.info("PostgreSQL jadvallari (users, listings...) muvaffaqiyatli tekshirildi/yaratildi!")
        except Exception as e:
            logging.error(f"Ma'lumotlar bazasi jadvallarini yaratishda xato: {e}")
    else:
        logging.error("DATABASE_URL topilmadi!")

    # 4. Redis ulanishi
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

    # Middleware va Routerlar
    dp.message.middleware(AntiSpamMiddleware(redis=redis, limit=2))
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
    

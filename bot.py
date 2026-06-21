import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from app.config import settings
from app.handlers import start, listing, admin, profile
from app.middlewares.antispam import AntiSpamMiddleware

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    # Redis ulanishi
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
                password=getattr(settings, "REDISPASSWORD", getattr(settings, "REDIS_PASSWORD", None)),
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
    

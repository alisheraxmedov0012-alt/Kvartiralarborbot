import time
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from redis.asyncio import Redis

class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis, limit: int = 2):
        self.redis = redis
        self.limit = limit
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not event.from_user:
            return await handler(event, data)
        
        user_id = event.from_user.id
        key = f"spam:{user_id}"
        
        last_time = await self.redis.get(key)
        current_time = time.time()
        
        if last_time and current_time - float(last_time) < self.limit:
            return await event.answer("⚠️ Iltimos, juda ko'p xabar yubormang (Anti-spam)!")
        
        await self.redis.set(key, str(current_time), ex=self.limit)
        return await handler(event, data)
      

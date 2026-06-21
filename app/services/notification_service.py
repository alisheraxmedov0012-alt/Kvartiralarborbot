from aiogram import Bot

class NotificationService:
    @staticmethod
    async def notify_user(bot: Bot, tg_id: int, text: str):
        try:
            await bot.send_message(chat_id=tg_id, text=text)
        except Exception:
            pass # Foydalanuvchi botni bloklagan bo'lishi mumkin
          

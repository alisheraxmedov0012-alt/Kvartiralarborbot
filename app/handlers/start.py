from aiogram import Router, Command
from aiogram.types import Message
from app.keyboards.user import main_menu
from app.database.session import async_session
from app.database.queries import get_or_create_user

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    # Referral aniqlash
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        
    async with async_session() as session:
        await get_or_create_user(
            session=session,
            tg_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
            referrer_id=referrer_id
        )
        
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}!\n"
        f"Samarqand Kvartira E'lonlari botiga xush kelibsiz.",
        reply_markup=main_menu()
    )

@router.message(lambda msg: msg.text == "👥 Taklifnomalar (Referral)")
async def cmd_referral(message: Message):
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    await message.answer(f"🔗 Sizning taklif havolangiz:\n{ref_link}\n\nHar bir taklif qilingan foydalanuvchi uchun tizim mukofot taqdim etishi mumkin.")
  

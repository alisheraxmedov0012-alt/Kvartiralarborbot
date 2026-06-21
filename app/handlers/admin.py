from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from app.config import settings
from app.keyboards.admin import admin_menu
from app.database.session import async_session
from app.database import queries
from app.database.models import ListingStatus
from app.services.channel_service import ChannelService
from app.services.notification_service import NotificationService

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in settings.admins:
        return await message.answer("Siz admin emassiz!")
    await message.answer("Admin panelga xush kelibsiz.", reply_markup=admin_menu())

@router.message(lambda msg: msg.text == "📊 Statistika")
async def admin_stats(message: Message):
    if message.from_user.id not in settings.admins: return
    async with async_session() as session:
        stats = await queries.get_stats(session)
    await message.answer(
        f"📊 Bot statistikasi:\n\n"
        f"👥 Jami foydalanuvchilar: {stats['users']}\n"
        f"📦 Jami e'lonlar: {stats['listings']}\n"
        f"⏳ Kutilayotgan e'lonlar: {stats['pending']}"
    )

@router.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in settings.admins: return
    listing_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        listing = await queries.update_listing_status(session, listing_id, ListingStatus.APPROVED)
        if listing:
            photos = await queries.get_photos_by_listing(session, listing_id)
            user = listing.user # Lazy load o'rniga queriesda eager olingan deb hisoblaymiz yoki session orqali
            # Kanalga chiqarish
            await ChannelService.post_to_channel(bot, listing, photos)
            # Userga bildirishnoma
            await NotificationService.notify_user(bot, 1, "✅ E'loningiz tasdiqlandi va kanalga joylandi!")
    
    await callback.message.edit_text("✅ Tasdiqlandi va kanalga yuborildi.")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in settings.admins: return
    listing_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        await queries.update_listing_status(session, listing_id, ListingStatus.REJECTED)
        
    await callback.message.edit_text("❌ E'lon rad etildi.")
    await callback.answer()
  

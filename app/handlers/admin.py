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
import logging

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in settings.admins:
        return await message.answer("Siz admin emassiz!")
    await message.answer("Admin paneliga xush kelibsiz.", reply_markup=admin_menu())

@router.message(lambda msg: msg.text == "📊 Statistika")
async def admin_stats(message: Message):
    if message.from_user.id not in settings.admins: 
        return
        
    async with async_session() as session:
        stats = await queries.get_stats(session)
        
    await message.answer(
        f"📊 Bot statistikasi:\n\n"
        f"👥 Jami foydalanuvchilar: {stats['users']}\n"
        f"🏠 Jami e'lonlar: {stats['listings']}\n"
        f"⏳ Kutilayotgan e'lonlar: {stats['pending']}"
    )

# TASDIQLASH (approve) tugmasi bosilganda
@router.callback_query(F.data.startswith("approve_") | F.data.startswith("admin_approve_"))
async def admin_approve(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in settings.admins: 
        return
        
    # Kalit nomidan qat'iy nazar faqat oxiridagi ID raqamni olish
    listing_id = int(callback.data.split("_")[-1])
    
    async with async_session() as session:
        listing = await queries.update_listing_status(session, listing_id, ListingStatus.APPROVED)
        if listing:
            photos = await queries.get_photos_by_listing(session, listing_id)
            
            # Kanalga chiqarish
            try:
                await ChannelService.post_to_channel(bot, listing, photos)
            except Exception as e:
                logging.error(f"Kanalga joylashda xato: {e}")
                
            # Userga bildirishnoma
            try:
                await NotificationService.notify_user(bot, listing.user_id, "✅ E'loningiz tasdiqlandi va kanalga joylandi!")
            except Exception:
                pass
                
    await callback.message.edit_text("✅ Tasdiqlandi va kanalga yuborildi.")
    await callback.answer()

# RAD ETISH (reject) tugmasi bosilganda
@router.callback_query(F.data.startswith("reject_") | F.data.startswith("admin_reject_"))
async def admin_reject(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in settings.admins: 
        return
        
    listing_id = int(callback.data.split("_")[-1])
    
    async with async_session() as session:
        await queries.update_listing_status(session, listing_id, ListingStatus.REJECTED)
        
    await callback.message.edit_text("❌ E'lon rad etildi.")
    await callback.answer()
    

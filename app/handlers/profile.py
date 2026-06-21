from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.database.session import async_session
from app.database import queries
from app.keyboards.user import listing_manage_keyboard
from app.services.listing_service import ListingService

router = Router()

@router.message(F.text == "🗂 Mening e'lonlarim")
async def my_listings(message: Message):
    async with async_session() as session:
        listings = await queries.get_user_listings(session, message.from_user.id)
    
    if not listings:
        return await message.answer("Sizda hali e'lonlar yo'q.")
        
    for listing in listings:
        status_emoji = "⏳" if listing.status.value == "pending" else "✅" if listing.status.value == "approved" else "❌"
        text = (
            f"E'lon ID: {listing.id}\n"
            f"Holati: {status_emoji} {listing.status.value.upper()}\n"
            f"Kvartira: {listing.rooms} xonali - {listing.price}"
        )
        await message.answer(text, reply_markup=listing_manage_keyboard(listing.id))

@router.callback_query(F.data.startswith("delete_"))
async def delete_listing_callback(callback: CallbackQuery):
    listing_id = int(callback.data.split("_")[1])
    success = await ListingService.delete_listing(listing_id)
    if success:
        await callback.message.edit_text("🗑 E'lon muvaffaqiyatli o'chirildi.")
    else:
        await callback.answer("Xatolik: E'lon topilmadi.", show_alert=True)
    await callback.answer()
  

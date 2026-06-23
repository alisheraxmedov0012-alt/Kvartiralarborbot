from aiogram import Bot
from app.config import settings
from app.database.models import Listing
from aiogram.types import InputMediaPhoto

class ChannelService:
    @staticmethod
    async def post_to_channel(bot: Bot, listing: Listing, photos: list):
        vip_tag = "⭐ VIP " if listing.is_vip else "🏠 "
        
        # Kanalga chiqadigan chiroyli va to'liq xabar matni
        caption = (
            f"{vip_tag}{listing.rooms} xonali kvartira\n\n"
            f"📍 Viloyat: {listing.region}\n"
            f"📌 Tuman/Manzil: {listing.district}, {listing.address}\n"
            f"🏢 Qavat: {listing.floor}\n"
            f"💰 Narx: {listing.price}\n"
            f"📞 Tel: {listing.phone}\n\n"
            f"📝 Tavsif: {listing.description}"
        )
        
        if not photos:
            await bot.send_message(chat_id=settings.CHANNEL_ID, text=caption)
        elif len(photos) == 1:
            await bot.send_photo(chat_id=settings.CHANNEL_ID, photo=photos[0].telegram_file_id, caption=caption)
        else:
            media = [InputMediaPhoto(media=photos[0].telegram_file_id, caption=caption)]
            for p in photos[1:]:
                media.append(InputMediaPhoto(media=p.telegram_file_id))
            await bot.send_media_group(chat_id=settings.CHANNEL_ID, media=media)
            

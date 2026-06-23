from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from app.states.listing import ListingState
from app.keyboards import user as kb
from app.config import settings
from app.keyboards.admin import admin_decision_keyboard
from app.database.session import async_session
from sqlalchemy import text

router = Router()

@router.message(F.text == "➕ E'lon berish")
async def start_listing_fsm(message: Message, state: FSMContext, redis):
    limit_key = f"limit:{message.from_user.id}"
    count = await redis.get(limit_key)
    if count and int(count) >= 3:
        return await message.answer("⚠️ Siz bugungi e'lon berish limitiga (3 ta) yetdingiz.")

    await state.set_state(ListingState.region)
    await message.answer("Viloyatni kiriting (Masalan: Samarqand):")

@router.message(ListingState.region)
async def process_region(message: Message, state: FSMContext):
    await state.update_data(region=message.text)
    await state.set_state(ListingState.district)
    await message.answer("Tuman yoki shaharni kiriting (Masalan: Samarqand shahar):")

@router.message(ListingState.district)
async def process_district(message: Message, state: FSMContext):
    await state.update_data(district=message.text)
    await state.set_state(ListingState.address)
    await message.answer("Aniq manzilni kiriting (Masalan: Kimyogarlar mavzesi):")

@router.message(ListingState.address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(ListingState.rooms)
    await message.answer("Xonalar sonini kiriting (Raqam bilan):")

@router.message(ListingState.rooms)
async def process_rooms(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Iltimos, faqat raqam kiriting:")
    await state.update_data(rooms=message.text)
    await state.set_state(ListingState.floor)
    await message.answer("Qavatni kiriting (Masalan: 4-qavat yoki 2/5):")

@router.message(ListingState.floor)
async def process_floor(message: Message, state: FSMContext):
    await state.update_data(floor=message.text)
    await state.set_state(ListingState.price)
    await message.answer("Narxni kiriting (Masalan: 350$):")

@router.message(ListingState.price)
async def process_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(ListingState.phone)
    await message.answer("Telefon raqamingizni kiriting:")

@router.message(ListingState.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text, phone_number=message.text)
    await state.set_state(ListingState.description)
    await message.answer("Tavsif yozing (Remonti, jihozlari haqida):")

@router.message(ListingState.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(ListingState.photos)
    await state.update_data(photos=[])
    await message.answer("E'lon rasmlarini yuboring (1 tadan 10 tagacha). Rasmlarni yuborib bo'lgach 'Tayyor' so'zini yozing:")

@router.message(ListingState.photos, F.photo)
async def process_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    if len(photos) >= 10:
        return
    
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    
    if len(photos) == 1 or len(photos) % 3 == 0:
        await message.answer(f"📸 {len(photos)} ta rasm yuklandi. Tugagach, 'Tayyor' deb yozing.")

@router.message(ListingState.photos, F.text.casefold() == "tayyor")
async def process_photos_ready(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get('photos'):
        return await message.answer("Iltimos, kamida bitta rasm yuklang.")
    
    await state.set_state(ListingState.preview)
    
    user_phone = data.get("phone") or data.get("phone_number") or "Kiritilmagan"
    preview_text = (
        f"🏠 {data['rooms']} xonali kvartira\n\n"
        f"📍 {data['region']}\n"
        f"📌 {data['district']}, {data['address']}\n\n"
        f"🏢 {data['floor']}\n"
        f"💰 {data['price']}\n\n"
        f"📞 {user_phone}\n\n"
        f"📝 {data['description']}"
    )
    
    photos = data['photos']
    if len(photos) == 1:
        await message.answer_photo(photo=photos[0], caption=preview_text, reply_markup=kb.confirmation_keyboard())
    else:
        media = [InputMediaPhoto(media=photos[0], caption=preview_text)]
        for p in photos[1:]:
            media.append(InputMediaPhoto(media=p))
        await message.answer_media_group(media=media)
        await message.answer("Ma'lumotlar to'g'rimi?", reply_markup=kb.confirmation_keyboard())

@router.callback_query(F.data == "confirm_listing", ListingState.preview)
async def confirm_listing_cb(callback: CallbackQuery, state: FSMContext, redis):
    data = await state.get_data()
    
    user_phone = data.get("phone") or data.get("phone_number") or "Kiritilmagan"
    
    # Ma'lumotlarni to'g'ridan-to'g'ri SQL so'rov orqali saqlash
    async with async_session() as session:
        query = text("""
            INSERT INTO listings (user_id, region, district, address, rooms, floor, price, phone, description, status)
            VALUES (:user_id, :region, :district, :address, :rooms, :floor, :price, :phone, :description, 'PENDING')
            RETURNING id;
        """)
        
        result = await session.execute(query, {
            "user_id": callback.from_user.id,
            "region": data.get("region"),
            "district": data.get("district"),
            "address": data.get("address"),
            "rooms": data.get("rooms"),
            "floor": data.get("floor"),
            "price": data.get("price"),
            "phone": user_phone,
            "description": data.get("description")
        })
        listing_id = result.scalar()
        await session.commit()
    
    limit_key = f"limit:{callback.from_user.id}"
    await redis.incr(limit_key)
    await redis.expire(limit_key, 86400)
    
    await callback.message.answer("✅ E'loningiz qabul qilindi va tahlilga yuborildi. Admin tasdiqlaganidan so'ng kanalga chiqadi.")
    
    for admin_id in settings.admins:
        try:
            admin_msg = (
                f"🆕 Yangi e'lon\n\n"
                f"Foydalanuvchi: {callback.from_user.full_name}\n"
                f"ID: {callback.from_user.id}\n\n"
                f"🏠 {data.get('rooms')} xonali kvartira\n"
                f"💰 Narxi: {data.get('price')}"
            )
            await callback.bot.send_message(chat_id=admin_id, text=admin_msg, reply_markup=admin_decision_keyboard(listing_id))
        except Exception:
            pass
            
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "confirm_listing", ListingState.preview)
async def confirm_listing_cb(callback: CallbackQuery, state: FSMContext, redis):
    data = await state.get_data()
    photos = data.get('photos', [])
    
    user_phone = data.get("phone") or data.get("phone_number") or "Kiritilmagan"
    
    # 1. Ma'lumotlarni bazaga yozish
    async with async_session() as session:
        query = text("""
            INSERT INTO listings (user_id, region, district, address, rooms, floor, price, phone, description, status)
            VALUES (:user_id, :region, :district, :address, :rooms, :floor, :price, :phone, :description, 'PENDING')
            RETURNING id;
        """)
        
        result = await session.execute(query, {
            "user_id": callback.from_user.id,
            "region": data.get("region"),
            "district": data.get("district"),
            "address": data.get("address"),
            "rooms": data.get("rooms"),
            "floor": data.get("floor"),
            "price": data.get("price"),
            "phone": user_phone,
            "description": data.get("description")
        })
        listing_id = result.scalar()
        await session.commit()
    
    # Limitni yangilash
    limit_key = f"limit:{callback.from_user.id}"
    await redis.incr(limit_key)
    await redis.expire(limit_key, 86400)
    
    await callback.message.answer("✅ E'loningiz qabul qilindi va tahlilga yuborildi. Admin tasdiqlaganidan so'ng kanalga chiqadi.")
    
    # 2. Adminga to'liq ma'lumot va rasmlarni yuborish mantiqi
    full_admin_msg = (
        f"🆕 Yangi e'lon (ID: {listing_id})\n\n"
        f"👤 Foydalanuvchi: {callback.from_user.full_name} (ID: {callback.from_user.id})\n\n"
        f"🏠 {data.get('rooms')} xonali kvartira\n"
        f"📍 Viloyat: {data.get('region')}\n"
        f"📌 Tuman/Manzil: {data.get('district')}, {data.get('address')}\n"
        f"🏢 Qavat: {data.get('floor')}\n"
        f"💰 Narx: {data.get('price')}\n"
        f"📞 Tel: {user_phone}\n\n"
        f"📝 Tavsif: {data.get('description')}"
    )
    
    for admin_id in settings.admins:
        try:
            if photos:
                # Agar rasmlar bo'lsa, birinchi rasmga matnni ulab albom qilib yuboramiz
                media = [InputMediaPhoto(media=photos[0], caption=full_admin_msg)]
                for p in photos[1:]:
                    media.append(InputMediaPhoto(media=p))
                
                await callback.bot.send_media_group(chat_id=int(admin_id), media=media)
                # Tugmalarni rasmlar ostidan alohida xabar qilib yuboramiz (Telegram qoidasi bo'yicha albomga to'g'ridan-to'g'ri tugma ulab bo'lmaydi)
                await callback.bot.send_message(
                    chat_id=int(admin_id), 
                    text="⚙️ Ushbu e'lonni tekshiring:", 
                    reply_markup=admin_decision_keyboard(listing_id)
                )
            else:
                # Agar rasm bo'lmasa, faqat matn va tugmaning o'zini yuboramiz
                await callback.bot.send_message(
                    chat_id=int(admin_id), 
                    text=full_admin_msg, 
                    reply_markup=admin_decision_keyboard(listing_id)
                )
        except Exception as e:
            import logging
            logging.error(f"Adminga yuborishda xato: {e}")
            
    await state.clear()
    await callback.answer()
    
    

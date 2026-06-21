from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ E'lon berish"), KeyboardButton(text="🗂 Mening e'lonlarim")],
            [KeyboardButton(text="🔍 Qidiruv"), KeyboardButton(text="🏆 Premium / VIP")],
            [KeyboardButton(text="👥 Taklifnomalar (Referral)"), KeyboardButton(text="💳 Balans / To'lov")]
        ],
        resize_keyboard=True
    )

def confirmation_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_listing"),
                InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="edit_listing")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_listing")
            ]
        ]
    )

def edit_fields_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Xonalar", callback_data="edit_rooms"), InlineKeyboardButton(text="Narx", callback_data="edit_price")],
            [InlineKeyboardButton(text="Tavsif", callback_data="edit_description"), InlineKeyboardButton(text="Manzil", callback_data="edit_address")]
        ]
    )

def listing_manage_keyboard(listing_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_{listing_id}")],
            [InlineKeyboardButton(text="⚡ VIP qilish", callback_data=f"make_vip_{listing_id}")]
        ]
    )
  

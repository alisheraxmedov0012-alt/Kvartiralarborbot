from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Kutilayotgan e'lonlar"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Reklama yuborish"), KeyboardButton(text="👥 Foydalanuvchilar")]
        ],
        resize_keyboard=True
    )

def admin_decision_keyboard(listing_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin_approve_{listing_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admin_reject_{listing_id}")
            ]
        ]
    )
  

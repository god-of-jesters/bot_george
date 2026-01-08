from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_registration_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.adjust(1)
    return keyboard.as_markup()

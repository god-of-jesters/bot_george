from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_registration_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Участник", callback_data="register_participant")
    keyboard.button(text="Организатор", callback_data="register_organizer")
    keyboard.adjust(1)
    return keyboard.as_markup()

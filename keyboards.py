from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def get_registration_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.adjust(1)
    return keyboard.as_markup()

def get_job_title_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Организаторы", callback_data="organizer")
    keyboard.button(text="Команда рейтинга", callback_data="rating_team")
    keyboard.button(text="РПГ-организаторы", callback_data="rpg_organizers")
    keyboard.button(text="Администраторы по комнатам", callback_data="room_administrators")
    keyboard.button(text="Команда медиа", callback_data="media_team")
    keyboard.button(text="Главный организатор", callback_data="chief_organizer")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_main_menu_student_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.button(text="Подать жалобу", callback_data="complaint")
    keyboard.button(text="Мои жалобы", callback_data="my_complaints")
    keyboard.button(text="Магазин", callback_data="shop")
    keyboard.button(text="Задать вопрос", callback_data="ask_question")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(1)
    return keyboard.as_markup()

def get_profile_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text="Главное меню")
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)
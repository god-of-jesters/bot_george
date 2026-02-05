from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

class DecisionCb(CallbackData, prefix="dec"):
    action: str   # "ok" | "no"
    req_id: int

class RoomComplaintCb(CallbackData, prefix="rc"):
    action: str   # "agree" | "disagree"
    complaint_id: int

def get_registration_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.adjust(1)
    return keyboard.as_markup()

def get_job_title_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Организаторы", callback_data="organizer")
    keyboard.button(text="Рейтинг", callback_data="rating_team")
    keyboard.button(text="РПГ", callback_data="rpg_organizers")
    keyboard.button(text="Администраторы", callback_data="room_administrators")
    keyboard.button(text="Медиа", callback_data="media_team")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_main_menu_student_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.button(text="Подать жалобу", callback_data="complaint")
    keyboard.button(text="Мои жалобы", callback_data="my_complaints")
    keyboard.button(text="Развлечения", callback_data="entertainment")
    keyboard.button(text="Обращение к администрации", callback_data="message_to_admin")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(1)
    return keyboard.as_markup()

def get_profile_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text="Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)

def get_main_menu_organizer_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.button(text="Подать жалобу", callback_data="complaint")
    keyboard.button(text="Жалобы в работе", callback_data="view_complaints")
    keyboard.button(text="Сообщить/Обратиться", callback_data="contact")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_main_menu_rpg_organizer_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.button(text="Редактировать товар", callback_data="edit_products")
    keyboard.button(text="Получить продажи", callback_data="get_sells")
    keyboard.button(text="Получить товары", callback_data="get_products")
    keyboard.button(text="Начислить валюту", callback_data="bonus")
    keyboard.button(text="Создать промокод", callback_data="create_promo")
    keyboard.button(text="Подать жалобу", callback_data="complaint")
    keyboard.button(text='Рассылка', callback_data='m')
    keyboard.button(text="Сообщить/Обратиться", callback_data="contact")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_main_menu_admins_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.button(text="Комантные обращения", callback_data="manage_rooms")
    keyboard.button(text="Рассылка", callback_data="mailing")
    keyboard.button(text="Подать жалобу", callback_data="complaint")
    keyboard.button(text="Сообщить/Обратиться", callback_data="contact")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_main_menu_rating_team_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.button(text="Жалобы", callback_data="view_complaints")
    keyboard.button(text="Участники", callback_data="participants")
    keyboard.button(text="Начисление и штрафы", callback_data="assign_rating")
    keyboard.button(text="Поощрение", callback_data="bonus")
    keyboard.button(text="Входящие сообщения", callback_data="inbox_messages")
    keyboard.button(text="Отправить жалобу", callback_data="complaint")
    keyboard.button(text="Рассылка", callback_data="mailing")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_main_menu_media_team_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.button(text="Рассылка", callback_data="mailing")
    keyboard.button(text="Сообщить/Обратиться", callback_data="contact")
    keyboard.button(text="Отправить жалобу", callback_data="complaint")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_complaint_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="На участника", callback_data="participant_behavior")
    keyboard.button(text="На организатора", callback_data="organizer_behavior")
    keyboard.button(text="На комнату", callback_data="room_problems")
    keyboard.button(text="На персонал базы", callback_data="other")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_complaint_category_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Срочно!", callback_data="alert")
    keyboard.button(text="В ближайщее время", callback_data="soon")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_finish_complaint_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Завершить жалобу", callback_data="complaint_done")
    kb.adjust(1)
    return kb.as_markup()

def get_yes_no_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data="yes")
    kb.button(text="Нет", callback_data="no")
    kb.adjust(1)
    return kb.as_markup()

def get_alert_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="1", callback_data="1")
    kb.button(text="2", callback_data="2")
    kb.button(text="3", callback_data="3")
    kb.button(text="4", callback_data="4")
    kb.button(text="5", callback_data="5")
    kb.button(text="6", callback_data="6")
    kb.adjust(3)
    return kb.as_markup()

def get_soon_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="1", callback_data="1")
    kb.button(text="2", callback_data="2")
    kb.button(text="3", callback_data="3")
    kb.button(text="4", callback_data="4")
    kb.adjust(2)
    return kb.as_markup()

def get_other_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="1", callback_data="1")
    kb.button(text="2", callback_data="2")
    kb.adjust(1)
    return kb.as_markup()

def get_violation_type_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="1", callback_data="1")
    kb.button(text="2", callback_data="2")
    kb.button(text="3", callback_data="3")
    kb.button(text="4", callback_data="4")
    kb.button(text="5", callback_data="5")
    kb.button(text="6", callback_data="6")
    kb.button(text="7", callback_data="7")
    kb.button(text="8", callback_data="8")
    kb.button(text="9", callback_data="9")
    kb.button(text="10", callback_data="10")
    kb.button(text="11", callback_data="11")
    kb.button(text="12", callback_data="12")
    kb.adjust(3)
    return kb.as_markup()

def get_agree_disagree_keyboard(complaint_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Согласиться",
        callback_data=RoomComplaintCb(action="agree", complaint_id=complaint_id).pack(),
    )
    kb.button(
        text="Не согласиться",
        callback_data=RoomComplaintCb(action="disagree", complaint_id=complaint_id).pack(),
    )
    kb.adjust(2)
    return kb.as_markup()

def get_users_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Все участники", callback_data="all_users")
    kb.button(text='Изменить данные участника', callback_data="edit_user_data")
    kb.button(text='Удалить участника', callback_data="del_user")
    kb.button(text="Назад в главное меню", callback_data="back_to_main_menu")
    kb.adjust(1)
    return kb.as_markup()

def get_upload_csv_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Рейтинг участников", callback_data="upload_rating_participants")
    kb.button(text="Рейтинг команд", callback_data="upload_rating_teams")
    kb.button(text="Загрузка участников", callback_data="upload_participants")
    kb.adjust(1)
    return kb.as_markup()

def get_export_csv_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Рейтинг участников", callback_data="export_rating_participants")
    kb.button(text="Рейтинг команд", callback_data="export_rating_teams")
    kb.button(text="Участники", callback_data="export_participants")
    kb.button(text="Выгрузить логи", callback_data="export_logs")
    kb.adjust(1)
    return kb.as_markup()

def get_edit_badge_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="ФИО", callback_data=f"fio")
    kb.button(text="Команда", callback_data=f"team_number")
    kb.button(text="Роль", callback_data=f"role")
    kb.button(text="Номер бейджа", callback_data=f"badge_number")
    kb.button(text="Рейтинг", callback_data=f"reiting")
    kb.button(text="Баланс", callback_data=f"balance")
    kb.button(text="Назад", callback_data="edit_user_back")
    kb.adjust(1)
    return kb.as_markup()

def get_student_entertainment_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text='Магазин', callback_data='shop')
    kb.button(text='ЗАГС', callback_data='zags')
    kb.button(text='Назад', callback_data='back_to_main_menu')
    kb.adjust(2)
    return kb.as_markup()

def get_student_help_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text='Правила и обязанности участника', callback_data='rules')
    kb.button(text='Помощь по работе с ботом', callback_data='help_in_work')
    kb.button(text='Назад', callback_data='back_to_main_menu')
    kb.adjust(1)
    return kb.as_markup()

def get_main_menu_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text='Главное меню', callback_data='main_menu')
    kb.adjust(1)
    return kb.as_markup()

def get_student_shop_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text='Товары и услуги', callback_data='products')
    kb.button(text='Мои покупки', callback_data='my_buy')
    kb.button(text='Задания', callback_data='tasks')
    kb.button(text='Ввести промокод', callback_data='give_promo')
    kb.button(text='Назад', callback_data='back_to_main_menu')
    kb.adjust(2)
    return kb.as_markup()

def get_buy_choice():
    kb = InlineKeyboardBuilder()
    kb.button(text='Купить себе', callback_data='for_me')
    kb.button(text='Подарить', callback_data='gift')
    kb.button(text='Назад', callback_data='back_to_main_menu')
    kb.adjust(1)
    return kb.as_markup()

def get_buy_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text='Приобрести', callback_data='buy')
    kb.button(text='Отказаться', callback_data='cancel')
    kb.adjust(1)
    return kb.as_markup()

def get_student_tasks_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text='Задания', callback_data='tasks')
    kb.button(text='Назад', callback_data='back_to_main_menu')
    kb.adjust(1)
    return kb.as_markup()

def get_student_zags_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text='Свадьба', callback_data='married')
    kb.button(text='Назад', callback_data='back_to_main_menu')
    kb.adjust(1)
    return kb.as_markup()

def get_room_admins_complaints():
    kb = InlineKeyboardBuilder()
    kb.button(text='Новые', callback_data='new')
    kb.button(text='В работе', callback_data='working')
    kb.button(text='Завершенные', callback_data='done')
    kb.adjust(1)
    return kb.as_markup()

def get_maling_adresat():
    kb = InlineKeyboardBuilder()
    kb.button(text='Участнику или организатору', callback_data='user')
    kb.button(text='Команде', callback_data='team')
    kb.button(text='Треку', callback_data='trek')
    kb.button(text='Всем', callback_data='all')
    kb.adjust(1)
    return kb.as_markup()

def get_bonus_adresat():
    kb = InlineKeyboardBuilder()
    kb.button(text='Участнику', callback_data='user')
    kb.button(text='Команде', callback_data='team')
    kb.button(text='Всем', callback_data='all')
    kb.adjust(1)
    return kb.as_markup()

def get_rating_choice_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text='Начислить', callback_data='add')
    kb.button(text='Штраф', callback_data='subtract')
    kb.adjust(1)
    return kb.as_markup()

def get_message_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text='Просмотрено', callback_data='seen')
    kb.button(text='Пропустить', callback_data='skip')
    kb.adjust(1)
    return kb.as_markup()

def decision_kb(req_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="Согласиться", callback_data=DecisionCb(action="ok", req_id=req_id).pack())
    kb.button(text="Не согласиться", callback_data=DecisionCb(action="no", req_id=req_id).pack())
    kb.adjust(2)
    return kb.as_markup()

def get_edit_product_choice():
    kb = InlineKeyboardBuilder()
    kb.button(text='Добавить товар', callback_data='add')
    kb.button(text='Редактировать товар', callback_data='update')
    kb.button(text='Удалить товар', callback_data='del')
    kb.adjust(1)
    return kb.as_markup()

def get_product_edit_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Изменить название", callback_data="name")
    kb.button(text="Изменить цену", callback_data="cost")
    kb.button(text="Изменить количество", callback_data="amount")
    kb.adjust(1)
    return kb.as_markup()

def get_married_second_name():
    kb = InlineKeyboardBuilder()
    kb.button(text="Оставить мою", callback_data="mine")
    kb.button(text="Оставить его/ее", callback_data="his")
    kb.adjust(1)
    return kb.as_markup()
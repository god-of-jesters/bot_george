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
    keyboard.adjust(2)
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
    keyboard.button(text="Рассылка", callback_data="mailing")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_main_menu_rpg_organizer_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.button(text="Магазин", callback_data="shop")
    keyboard.button(text="Операции с участниками", callback_data="operations_with_participants")
    keyboard.button(text="История операций", callback_data="operation_history")
    keyboard.button(text="Рассылка", callback_data="mailing")
    keyboard.button(text="Сообщить/Обратиться", callback_data="contact")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_main_menu_admins_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.button(text="Комантные обращения", callback_data="manage_rooms")
    keyboard.button(text="Рассылка", callback_data="mailing")
    keyboard.button(text="Журнал действий", callback_data="activity_log")
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
    keyboard.button(text="Входящие сообщения", callback_data="inbox_messages")
    keyboard.button(text="Рассылка", callback_data="mailing")
    keyboard.button(text="Безопастность", callback_data="security")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_main_menu_chief_organizer_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.button(text="Управление командой", callback_data="team_management")
    keyboard.button(text="Жалобы", callback_data="view_complaints")
    keyboard.button(text="Рассылка", callback_data="mailing")
    keyboard.button(text="Отчеты и аналитика", callback_data="reports_analytics")
    keyboard.button(text="Сообщить/Обратиться", callback_data="contact")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_main_menu_media_team_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Профиль", callback_data="profile")
    keyboard.button(text="Галерея", callback_data="gallery")
    keyboard.button(text="Расписание съемок", callback_data="shooting_schedule")
    keyboard.button(text="Загрузка материалов", callback_data="upload_materials")
    keyboard.button(text="Рассылка", callback_data="mailing")
    keyboard.button(text="Сообщить/Обратиться", callback_data="contact")
    keyboard.button(text="Помощь", callback_data="help")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_complaint_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="На участника", callback_data="participant_behavior")
    keyboard.button(text="На организатора", callback_data="organizer_behavior")
    keyboard.button(text="На комнату", callback_data="room_issue")
    keyboard.button(text="На персонал базы", callback_data="other")
    keyboard.adjust(2)
    return keyboard.as_markup()

def get_complaint_category_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Срочно!", callback_data="alert")
    keyboard.button(text="В ближайщее время", callback_data="soon")
    keyboard.button(text="Жалоба на комнату", callback_data="room_problems")
    keyboard.button(text="Иное", callback_data="other_issues")
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

def get_agree_disagree_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Согласиться", callback_data="agree")
    kb.button(text="Оспорить", callback_data="disagree")
    kb.adjust(1)
    return kb.as_markup()

def get_users_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Все участники", callback_data="all_users")
    kb.button(text='Изменить данные участника', callback_data="edit_user_data")
    kb.button(text="Назад в главное меню", callback_data="back_to_main_menu")
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
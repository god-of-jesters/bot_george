from aiogram.fsm.state import State, StatesGroup

class Reg(StatesGroup):
    waiting_for_fio = State()
    waiting_for_bage_number = State()
    waiting_for_team_number = State()
    waiting_for_job_title = State()

class MainMenu(StatesGroup):
    main_menu_student = State()
    main_menu_organizer = State()
    main_menu_rpg_organizer = State()
    main_menu_admins = State()
    main_menu_rating_team = State()
    main_menu_media_team = State()
    main_menu_chief_organizer = State()
    profile = State()
    complaint = State()
    users = State()
    student_entertainment = State()
    student_help = State()
    message_to_admin = State()
    message_to_rating_team = State()

class ComplaintProcess(StatesGroup):
    waiting_for_complaint_text = State()
    waiting_for_badge = State()
    waiting_for_violation_type = State()
    waiting_for_complaint_category = State()
    waiting_for_complaint_files = State()
    waiting_for_complaint_confirmation = State()

class YesNoChoice(StatesGroup):
    waiting_for_alarm_complaint = State()
    waiting_for_verdict = State()

class ComplaintReview(StatesGroup):
    stat = State()
    safe = State()
    main = State()

class UserDataEdit(StatesGroup):
    waiting_for_badge_number = State()
    waiting_for_change_choice = State()
    waiting_for_new_value = State()

class Mailing(StatesGroup):
    waiting_for_mailing_text = State()
    waiting_adresat = State()
    waiting_info = State()

class RatingCSV(StatesGroup):
    waiting_for_upload_choice = State()
    waiting_for_export_choice = State()
    waiting_for_csv = State()

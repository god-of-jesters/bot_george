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
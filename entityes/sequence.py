from aiogram.fsm.state import State, StatesGroup

class Reg(StatesGroup):
    waiting_for_fio = State()
    waiting_for_bage_number = State()
    waiting_for_team_number = State()
    waiting_for_job_title = State()

class MainMenu(StatesGroup):
    main_menu = State()
    profile = State()

class ComplaintProcess(StatesGroup):
    waiting_for_complaint_text = State()
    waiting_for_complaint_confirmation = State()
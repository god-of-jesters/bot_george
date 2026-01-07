from aiogram.fsm.state import State, StatesGroup

class Reg(StatesGroup):
    waiting_for_fio = State()
    waiting_for_bage_number = State()
    waiting_for_team_number = State()
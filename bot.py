import asyncio

from aiogram.filters.callback_data import CallbackData
from aiogram import Bot, Dispatcher, Router
from aiogram.types import CallbackQuery
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

from database import *
from repo.user_repo import *
from repo.file_repo import *

from entityes.registration import Reg

from keyboards import get_registration_keyboard
import logging

logging.basicConfig(level=logging.INFO)

API_TOKEN = open("API.txt", "r", encoding="utf-8").read().strip()
active_sessions = {}
registration = {}
router = Router()

@router.message(Command("teg"))
async def cmd_teg(message: Message):
    id = message.from_user.id
    await message.answer(f"{id}")

@router.callback_query()
async def handle_actions(callback: CallbackQuery, state: FSMContext):
    id = callback.from_user.id
    await callback.message.answer("Введите ФИО полностью.")

    await callback.message.delete()

    match callback.data:
        case "register_participant":
            registration[id].role = 'participant'

        case "register_organizer":
            registration[id].role = 'organizer'
    await state.set_state(Reg.waiting_for_fio)

@router.message(Reg.waiting_for_fio)
async def process_fio(message: Message, state: FSMContext):
    user_id = message.from_user.id
    registration[user_id].fio = message.text

    await message.answer("Введите номер бейджа.")
    await state.set_state(Reg.waiting_for_bage_number)

@router.message(Reg.waiting_for_bage_number)
async def process_badge_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    registration[user_id].badge_number = int(message.text)

    await message.answer("Введите номер команды.")
    await state.set_state(Reg.waiting_for_team_number)

@router.message(Reg.waiting_for_team_number)
async def process_team_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    registration[user_id].team_number = int(message.text)

    await add_user(registration[user_id])

    del active_sessions[user_id]
    del registration[user_id]

    await message.answer("Регистрация завершена! Спасибо.")
    await state.clear()

async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not active_sessions.get(user_id):
        registration[user_id] = User(user_id=user_id)
        registration[user_id].tg_id = user_id
        active_sessions[user_id] = True
        await message.answer(
            "Приветствую! Для начала надо пройти регистрацию.\n"
            "Выберите роль на мероприятии.",
            reply_markup=get_registration_keyboard()
        )
    else:
        await message.answer("Вы уже начали регистрацию.")

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start_handler, CommandStart())
    dp.include_router(router)

    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
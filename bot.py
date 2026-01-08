import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

from database import *
from repo.team_repo import *
from repo.user_repo import *
from repo.file_repo import *

from entityes.sequence import Reg

from keyboards import get_job_title_keyboard, get_registration_keyboard
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()
API_TOKEN = os.getenv("BOT")
active_sessions = {}
registration = {}
router = Router()
teams = {team.team_number: team for team in get_all_teams()}

@router.message(Command("teg"))
async def cmd_teg(message: Message):
    id = message.from_user.id
    await message.answer(f"{id}")

@router.message(Reg.waiting_for_fio)
async def process_fio(message: Message, state: FSMContext):
    user_id = message.from_user.id
    registration[user_id].fio = message.text

    with get_user_by_badge(registration[user_id].badge_number) as existing_user:
        if existing_user:
            if existing_user.fio != registration[user_id].fio:
                await message.answer("Пользователь с таким номером бейджа уже зарегистрирован с другим ФИО. Пожалуйста, проверьте введенные данные.")
                await state.set_state(Reg.waiting_for_bage_number)
                return
        
    await add_user(registration[user_id])

    active_sessions[user_id] = registration[user_id]
    del registration[user_id]

    await message.answer("Регистрация завершена! Спасибо.")
    await state.clear()

@router.message(Reg.waiting_for_bage_number)
async def process_badge_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        badge_number = int(message.text)
    except ValueError:
        await message.answer("Номер бейджа должен быть числом. Пожалуйста, введите номер бейджа еще раз.")
        return
    
    with get_user_by_badge(registration[user_id].badge_number) as existing_user:
        if not existing_user:
            await message.answer("Такого пользователя нет. Введите номер бейджа еще раз.")
            return
        
    registration[user_id].badge_number = int(message.text)

    await message.answer("Введите ФИО, все с большой буквы в именительном падеже.")
    await state.set_state(Reg.waiting_for_fio)

async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not active_sessions.get(user_id):
        registration[user_id] = User(user_id=user_id, tg_id=user_id)
        await message.answer(
            "Приветствую! Для начала надо пройти регистрацию.\n"
            "Введите ваш номер бейджа.",
        )
        await state.set_state(Reg.waiting_for_bage_number)
    else:
        main_menu = "Главное меню.\n" \
        f"ФИО: {registration[user_id].fio}\n Роль: {registration[user_id].role}\n" \
        f"Номер бейджа: {registration[user_id].num_badge}\n"
        main_menu += f"Название команды: {teams[registration[user_id].team_number].team_name}\n" if registration[user_id].team_number in teams else "Не назначена команда\n"
        main_menu += f"Рейтинг: {registration[user_id].reiting}\n"
        main_menu += f"Рейтинг команды: {teams[registration[user_id].team_number].reiting}\n" if registration[user_id].team_number in teams else ""
        main_menu += f"Баланс: {registration[user_id].balance} очков\n"
        await message.answer(main_menu)

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start_handler, CommandStart())
    dp.include_router(router)

    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
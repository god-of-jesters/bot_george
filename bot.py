import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

from database import load_datastore, USERS, TEAMS, FILES, COMPLAINTS
from repo.team_repo import *
from repo.user_repo import *
from repo.file_repo import *
from repo.complait_repo import *
from entityes.sequence import *

from keyboards import *
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()
API_TOKEN = os.getenv("BOT")
active_sessions = {}
registration = {}
complaintes = {}
router = Router()

@router.callback_query(Reg.waiting_for_job_title)
async def process_job_title_callback(callback_query, state: FSMContext):
    user_id = callback_query.from_user.id
    job_title = callback_query.data

    role_map = {
        "organizer": "Организатор",
        "rating_team": "Команда рейтинга",
        "rpg_organizers": "РПГ-организаторы",
        "room_administrators": "Администраторы по комнатам",
        "media_team": "Команда медиа",
        "chief_organizer": "Главный организатор"
    }

    if job_title in role_map:
        registration[user_id].role = role_map[job_title]
        await add_user(registration[user_id])

        active_sessions[user_id] = registration[user_id]
        del registration[user_id]

        await callback_query.message.answer("Регистрация завершена! Спасибо.")
        await state.clear()
    else:
        await callback_query.message.answer("Неверный выбор должности. Пожалуйста, выберите вашу должность еще раз.", reply_markup=get_job_title_keyboard()) 

@router.callback_query(MainMenu.main_menu)
async def show_profile(callback_query: Message, state: FSMContext):
    user_id = callback_query.from_user.id
    data = callback_query.data
    match data:
        case "profile":
            profile = "Профиль:\n"
            profile += f"ФИО: {active_sessions[user_id].fio}\n Роль: {active_sessions[user_id].role}\n"
            profile += f"Номер бейджа: {active_sessions[user_id].num_badge}\n"
            if active_sessions[user_id].role == "Участник":
                profile += f"Название команды: {teams[active_sessions[user_id].team_number].team_name}\n" if active_sessions[user_id].team_number in teams else "Не назначена команда\n"
                profile += f"Рейтинг: {active_sessions[user_id].reiting}\n"
                profile += f"Рейтинг команды: {teams[active_sessions[user_id].team_number].reiting}\n" if active_sessions[user_id].team_number in teams else ""
                profile += f"Баланс: {active_sessions[user_id].balance} очков\n"
                await callback_query.message.answer(profile, reply_markup=get_profile_keyboard())
                await state.set_state(MainMenu.profile)
        case "complaint":
            await callback_query.message.answer("На что будет жалоба.", reply_markup=get_complaint_keyboard())
            await state.set_state(MainMenu.complaint)

@router.callback_query(MainMenu.complaint)
async def process_complaint_callback(callback_query: Message, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    if user_id not in complaintes:
        complaintes[user_id] = Complaint(user_id=user_id, adresat=data, status="Новая")
    await callback_query.message.answer("Выберете категорию жалобы.", reply_markup=get_complaint_category_keyboard())
    await state.set_state(ComplaintProcess.waiting_for_complaint_text)

@router.callback_query(ComplaintProcess.waiting_for_complaint_category)
async def process_complaint_category_callback(callback_query: Message, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    if user_id in complaintes:
        complaintes[user_id].category = data
        await callback_query.message.answer("Опишите вашу жалобу подробно.")
        await state.set_state(ComplaintProcess.waiting_for_complaint_text)

@router.message(ComplaintProcess.waiting_for_complaint_text)
async def process_complaint_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in complaintes:
        complaintes[user_id].description = message.text
        await message.answer("При наличии доказательств, прикрепите их в следующем сообщении. Максимальное количество файлов: \n Фото - 3 (суммарно до 5мб)\n Видео - 1 (до 20мб)\n Если доказательств нет, отправьте команду /skip")
        await state.set_state(ComplaintProcess.waiting_for_complaint_files)
    
@router.message(Command("teg"))
async def cmd_teg(message: Message):
    id = message.from_user.id
    await message.answer(f"{id}")

@router.message(Command("skip"), ComplaintProcess.waiting_for_complaint_files)
async def skip_files(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in complaintes:
        await message.answer("Жалоба отправлена без файлов.")
        await state.clear()
        await add_complaint(complaintes[user_id])
        del complaintes[user_id]


@router.message(Reg.waiting_for_bage_number)
async def process_badge_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        badge_number = int(message.text)
    except ValueError:
        await message.answer("Номер бейджа должен быть числом. Пожалуйста, введите номер бейджа еще раз.")
        return
    existing_user = await get_user_by_badge(badge_number)
    if not existing_user:
        await message.answer("Такого пользователя нет. Введите номер бейджа еще раз.")
        return
    
    registration[user_id].badge_number = int(message.text)

    await message.answer("Введите ФИО, все с большой буквы в именительном падеже.")
    await state.set_state(Reg.waiting_for_fio)

@router.message(Reg.waiting_for_fio)
async def process_fio(message: Message, state: FSMContext):
    user_id = message.from_user.id
    registration[user_id].fio = message.text

    existing_user = await get_user_by_badge(registration[user_id].badge_number)
    if existing_user:
        if existing_user.fio != registration[user_id].fio:
            await message.answer("Пользователь с таким номером бейджа уже зарегистрирован с другим ФИО. Пожалуйста, проверьте введенные данные.")
            await state.set_state(Reg.waiting_for_bage_number)
            return
    
    if registration[user_id].badge_number >= 100 and registration[user_id].badge_number < 1000:
        registration[user_id].role = "Участник"
        await message.answer("Введите номер вашей команды.")
        await state.set_state(Reg.waiting_for_team_number)
    elif registration[user_id].badge_number >= 10 and registration[user_id].badge_number < 100:
        await message.answer("Выберете вашу должность.", reply_markup=get_job_title_keyboard())
        await state.set_state(Reg.waiting_for_job_title)
    else: 
        await message.answer("Неверный номер бейджа или роль. Пожалуйста, введите номер бейджа еще раз.")
    
@router.message(Reg.waiting_for_team_number)
async def process_team_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        team_number = int(message.text)
    except ValueError:
        await message.answer("Номер команды должен быть числом. Пожалуйста, введите номер команды еще раз.")
        return
    if team_number not in teams:
        await message.answer("Такой команды нет. Введите номер команды еще раз.")
        return
    
    await add_user(registration[user_id])

    active_sessions[user_id] = registration[user_id]
    del registration[user_id]

    await message.answer("Регистрация завершена! Спасибо.")
    await state.clear()

async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not active_sessions.get(user_id):
        registration[user_id] = User(user_id=user_id)
        await message.answer(
            "Приветствую! Для начала надо пройти регистрацию.\n"
            "Введите ваш номер бейджа.",
        )
        await state.set_state(Reg.waiting_for_bage_number)
    else:
        match active_sessions[user_id].role:
            case "Участник":
                await message.answer("Главное меню.", reply_markup=get_main_menu_student_keyboard())
                await state.set_state(MainMenu.main_menu)
            case "Организатор":
                await message.answer("Главное меню.", reply_markup=get_main_menu_organizer_keyboard())
                await state.set_state(MainMenu.main_menu)
            case "РПГ-организаторы":
                await message.answer("Главное меню.", reply_markup=get_main_menu_rpg_organizer_keyboard())
                await state.set_state(MainMenu.main_menu)
            case "Администраторы по комнатам":
                await message.answer("Главное меню.", reply_markup=get_main_menu_admins_keyboard())
                await state.set_state(MainMenu.main_menu)
            case "Команда рейтинга":
                await message.answer("Главное меню.", reply_markup=get_main_menu_rating_team_keyboard())
                await state.set_state(MainMenu.main_menu)
            case "Команда медиа":
                await message.answer("Главное меню.", reply_markup=get_main_menu_media_team_keyboard())
                await state.set_state(MainMenu.main_menu)
            case "Главный организатор":
                await message.answer("Главное меню.", reply_markup=get_main_menu_chief_organizer_keyboard())
                await state.set_state(MainMenu.main_menu)

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start_handler, CommandStart())
    dp.include_router(router)

    await load_datastore()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
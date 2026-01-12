import asyncio
import os
from dotenv import load_dotenv
from collections import defaultdict

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

from database import load_datastore, USERS, TEAMS, FILES, COMPLAINTS
from repo.team_repo import *
from repo.user_repo import *
from repo.file_repo import *
from repo.complaint_repo import *
from entityes.sequence import *

from keyboards import *
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()
API_TOKEN = os.getenv("BOT")
active_sessions = {}
registration = {}
complaintes = {}
_album_buffer: dict[tuple[int, str], list[Message]] = defaultdict(list)
_album_tasks: dict[tuple[int, str], asyncio.Task] = {}

ALBUM_FLUSH_DELAY = 0.7
router = Router()

@router.message(MainMenu.profile)
async def main_menu_callback(message: Message, state: FSMContext):
    user_id = message.from_user.id
    match active_sessions[user_id].role:
            case "Участник":
                await message.answer("Главное меню.", reply_markup=get_main_menu_student_keyboard())
            case "Организатор":
                await message.answer("Главное меню.", reply_markup=get_main_menu_organizer_keyboard())
            case "РПГ-организаторы":
                await message.answer("Главное меню.", reply_markup=get_main_menu_rpg_organizer_keyboard())
            case "Администраторы по комнатам":
                await message.answer("Главное меню.", reply_markup=get_main_menu_admins_keyboard())
            case "Команда рейтинга":
                await message.answer("Главное меню.", reply_markup=get_main_menu_rating_team_keyboard())
            case "Команда медиа":
                await message.answer("Главное меню.", reply_markup=get_main_menu_media_team_keyboard())
            case "Главный организатор":
                await message.answer("Главное меню.", reply_markup=get_main_menu_chief_organizer_keyboard())
    await state.set_state(MainMenu.main_menu)

@router.callback_query(lambda c: c.data == "complaint_done", ComplaintProcess.waiting_for_complaint_files)
async def finish_complaint_cb(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.answer()

    if user_id in complaintes:
        del complaintes[user_id]

    await callback.message.answer("Жалоба отправлена. Спасибо.")
    await show_main_menu(callback.bot, user_id, state)

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

@router.callback_query(MainMenu.main_menu_student)
async def show_profile(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    data = callback_query.data
    match data:
        case "profile":
            profile = "Профиль:\n"
            profile += f"ФИО: {active_sessions[user_id].fio}\n Роль: {active_sessions[user_id].role}\n"
            profile += f"Номер бейджа: {active_sessions[user_id].badge_number}\n"
            if active_sessions[user_id].role == "Участник":
                profile += f"Название команды: {TEAMS[active_sessions[user_id].team_number].team_name}\n" if active_sessions[user_id].team_number in TEAMS else "Не назначена команда\n"
                profile += f"Рейтинг: {active_sessions[user_id].reiting}\n"
                profile += f"Рейтинг команды: {TEAMS[active_sessions[user_id].team_number].reiting}\n" if active_sessions[user_id].team_number in TEAMS else ""
                profile += f"Баланс: {active_sessions[user_id].balance} очков\n"
                await callback_query.message.answer(profile, reply_markup=get_profile_keyboard())
                await state.set_state(MainMenu.profile)
        case "complaint":
            await callback_query.message.answer("На что будет жалоба.", reply_markup=get_complaint_keyboard())
            await state.set_state(MainMenu.complaint)

@router.callback_query(MainMenu.main_menu_organizer)
async def show_profile_organizer(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    data = callback_query.data
    role = getattr(active_sessions.get(user_id), "role", None)
    if role != "Организатор":
        return

    match data:
        case "profile":
            await callback_query.message.answer("Профиль организатора.", reply_markup=get_profile_keyboard())
            await state.set_state(MainMenu.profile)

        case "complaint":
            await callback_query.message.answer("Подать жалобу.", reply_markup=get_complaint_keyboard())
            await state.set_state(MainMenu.complaint)

        case "view_complaints":
            await callback_query.message.answer("Жалобы в работе.\n(Здесь будет очередь обращений.)")

        case "contact":
            await callback_query.message.answer("Сообщить/Обратиться.\n(Здесь будет форма сообщения.)")

        case "mailing":
            await callback_query.message.answer("Рассылка.\n(Здесь будет модуль рассылки.)")

        case "help":
            await callback_query.message.answer("Помощь.\n(Здесь будет справка для организаторов.)")

        case _:
            await callback_query.message.answer("Команда не распознана.")

@router.callback_query(MainMenu.main_menu_rpg_organizer)
async def show_profile_rpg_organizer(callback_query: Message, state: FSMContext):
    user_id = callback_query.from_user.id
    data = callback_query.data
    role = getattr(active_sessions.get(user_id), "role", None)
    if role != "РПГ-организаторы":
        return

    match data:
        case "profile":
            await callback_query.message.answer("Профиль РПГ-организатора.", reply_markup=get_profile_keyboard())
            await state.set_state(MainMenu.profile)

        case "shop":
            await callback_query.message.answer("Магазин.\n(Здесь будет магазин для РПГ-организаторов.)")

        case "operations_with_participants":
            await callback_query.message.answer("Операции с участниками.\n(Здесь будут операции с участниками.)")

        case "operation_history":
            await callback_query.message.answer("История операций.\n(Здесь будет история операций.)")

        case "mailing":
            await callback_query.message.answer("Рассылка.\n(Здесь будет модуль рассылки.)")

        case "contact":
            await callback_query.message.answer("Сообщить/Обратиться.\n(Здесь будет форма сообщения.)")

        case "help":
            await callback_query.message.answer("Помощь.\n(Здесь будет справка для РПГ-организаторов.)")

        case _:
            await callback_query.message.answer("Команда не распознана.")

@router.callback_query(MainMenu.main_menu_admins)
async def show_profile_admins(callback_query: Message, state: FSMContext):
    user_id = callback_query.from_user.id
    data = callback_query.data
    role = getattr(active_sessions.get(user_id), "role", None)
    if role != "Администраторы по комнатам":
        return

    match data:
        case "profile":
            await callback_query.message.answer("Профиль администратора по комнатам.", reply_markup=get_profile_keyboard())
            await state.set_state(MainMenu.profile)

        case "manage_rooms":
            await callback_query.message.answer("Комнатные обращения.\n(Здесь будет модуль управления комнатами.)")

        case "mailing":
            await callback_query.message.answer("Рассылка.\n(Здесь будет модуль рассылки.)")

        case "activity_log":
            await callback_query.message.answer("Журнал действий.\n(Здесь будет журнал действий.)")

        case "contact":
            await callback_query.message.answer("Сообщить/Обратиться.\n(Здесь будет форма сообщения.)")

        case "help":
            await callback_query.message.answer("Помощь.\n(Здесь будет справка для администраторов по комнатам.)")

        case _:
            await callback_query.message.answer("Команда не распознана.")

@router.callback_query(MainMenu.main_menu_rating_team)
async def show_profile_rating_team(callback_query: Message, state: FSMContext):
    user_id = callback_query.from_user.id
    data = callback_query.data
    role = getattr(active_sessions.get(user_id), "role", None)
    if role != "Команда рейтинга":
        return

    match data:
        case "profile":
            await callback_query.message.answer("Профиль команды рейтинга.", reply_markup=get_profile_keyboard())
            await state.set_state(MainMenu.profile)

        case "view_complaints":
            await callback_query.message.answer("Жалобы.\n(Здесь будет модуль работы с жалобами.)")

        case "participants":
            await callback_query.message.answer("Участники.\n(Здесь будет модуль работы с участниками.)")

        case "assign_rating":
            await callback_query.message.answer("Начисление и штрафы.\n(Здесь будет модуль начисления и штрафов.)")

        case "inbox_messages":
            await callback_query.message.answer("Входящие сообщения.\n(Здесь будут входящие сообщения.)")

        case "mailing":
            await callback_query.message.answer("Рассылка.\n(Здесь будет модуль рассылки.)")

        case "security":
            await callback_query.message.answer("Безопастность.\n(Здесь будет модуль безопасности.)")

        case "help":
            await callback_query.message.answer("Помощь.\n(Здесь будет справка для команды рейтинга.)")

        case _:
            await callback_query.message.answer("Команда не распознана.")

@router.callback_query(MainMenu.main_menu_chief_organizer)
async def show_profile_chief_organizer(callback_query: Message, state: FSMContext):
    user_id = callback_query.from_user.id
    data = callback_query.data
    role = getattr(active_sessions.get(user_id), "role", None)
    if role != "Главный организатор":
        return

    match data:
        case "profile":
            await callback_query.message.answer("Профиль главного организатора.", reply_markup=get_profile_keyboard())
            await state.set_state(MainMenu.profile)

        case "team_management":
            await callback_query.message.answer("Управление командой.\n(Здесь будет модуль управления командой.)")

        case "view_complaints":
            await callback_query.message.answer("Жалобы.\n(Здесь будет модуль работы с жалобами.)")

        case "mailing":
            await callback_query.message.answer("Рассылка.\n(Здесь будет модуль рассылки.)")

        case "reports_analytics":
            await callback_query.message.answer("Отчеты и аналитика.\n(Здесь будут отчеты и аналитика.)")

        case "contact":
            await callback_query.message.answer("Сообщить/Обратиться.\n(Здесь будет форма сообщения.)")

        case "help":
            await callback_query.message.answer("Помощь.\n(Здесь будет справка для главного организатора.)")

        case _:
            await callback_query.message.answer("Команда не распознана.")


@router.callback_query(MainMenu.complaint)
async def process_complaint_callback(callback_query: Message, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    if user_id not in complaintes:
        complaintes[user_id] = Complaint(user_id=user_id, adresat=data, status="Новая")
    await callback_query.message.answer("Выберете категорию жалобы.", reply_markup=get_complaint_category_keyboard())
    await state.set_state(ComplaintProcess.waiting_for_complaint_category)

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
        await message.answer("При наличии доказательств, прикрепите их в следующем сообщении. Отправьте фото или видео, или /skip чтобы завершить без файлов.")
        await state.set_state(ComplaintProcess.waiting_for_complaint_files)
    
@router.message(Command("teg"))
async def cmd_teg(message: Message):
    id = message.from_user.id
    await message.answer(f"{id}")

@router.message(Command("skip"), ComplaintProcess.waiting_for_complaint_files)
async def skip_files(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in complaintes:
        await message.answer("Завершить жалобу?", reply_markup=get_finish_complaint_keyboard())
        await state.clear()
        await add_complaint(complaintes[user_id])
        del complaintes[user_id]

@router.message(ComplaintProcess.waiting_for_complaint_files)
async def process_complaint_files(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in complaintes:
        return

    if message.photo:
        photo = message.photo[-1]
        file_id = photo.file_id
        file_size = photo.file_size
        mime_type = "image/jpeg"
        file_name = f"photo_{len(complaintes[user_id].files) + 1}.jpg"
        file = File(id=None, tg_id=user_id, tg_file_id=file_id, complaint_id=None, file_name=file_name, mime_type=mime_type, file_size=file_size)
        await add_file(file)
        complaintes[user_id].files.append(file.file_id)
        complaintes[user_id].photo_count += 1
        await message.answer("Фото добавлено. \nЖалоба отправлена!")
        await show_main_menu(message.bot, user_id, state)

    elif message.video:
        video = message.video
        file_id = video.file_id
        file_size = video.file_size
        mime_type = video.mime_type or "video/mp4"
        file_name = f"video_{len(complaintes[user_id].files) + 1}.mp4"
        file = File(id=None, tg_id=user_id, tg_file_id=file_id, complaint_id=None, file_name=file_name, mime_type=mime_type, file_size=file_size)
        await add_file(file)
        complaintes[user_id].files.append(file.file_id)
        complaintes[user_id].video_count += 1
        await message.answer("Видео добавлено. \nЖалоба отправлена!")
        await show_main_menu(message.bot, user_id, state)
    else:
        await message.answer("Пожалуйста, отправьте фото или видео, или /skip чтобы завершить.")

async def _flush_album(user_id: int, media_group_id: str, bot, chat_id: int):
    key = (user_id, media_group_id)
    messages = _album_buffer.pop(key, [])

    if not messages:
        return

    results = []
    for msg in messages:
        added, text = await try_add_media_to_complaint(msg, user_id)
        results.append(text)

    await bot.send_message(
        chat_id,
        "Альбом обработан:\n" + "\n".join(f"• {r}" for r in results) +
        "\n\nМожете отправить ещё или завершить жалобу.",
        reply_markup=get_finish_complaint_keyboard()
    )

async def try_add_media_to_complaint(message: Message, user_id: int):
    if user_id not in complaintes:
        return False, "Жалоба не найдена. Начните заново."

    complaint = complaintes[user_id]

    if not hasattr(complaint, "photo_count"):
        complaint.photo_count = 0
    if not hasattr(complaint, "video_count"):
        complaint.video_count = 0

    if message.photo:
        if complaint.photo_count >= 3:
            return False, f"Лимит фото: {3}. Доп. фото не принимаются."

        photo = message.photo[-1]
        file = File(
            id=None,
            tg_id=user_id,
            tg_file_id=photo.file_id,
            complaint_id=complaint.id,
            file_name=f"photo_{complaint.photo_count + 1}.jpg",
            mime_type="image/jpeg",
            file_size=photo.file_size
        )
        await add_file(file)

        complaint.photo_count += 1
        complaint.files.append(file.id)

        return True, f"Фото добавлено ({complaint.photo_count}/{3})."

    if message.video:
        if complaint.video_count >= 1:
            return False, f"Лимит видео: {1}. Доп. видео не принимаются."

        video = message.video
        file = File(
            id=None,
            tg_id=user_id,
            tg_file_id=video.file_id,
            complaint_id=complaint.id,
            file_name=video.file_name or f"video_{complaint.video_count + 1}.mp4",
            mime_type=video.mime_type or "video/mp4",
            file_size=video.file_size
        )
        await add_file(file)

        complaint.video_count += 1
        complaint.files.append(file.id)

        return True, f"Видео добавлено ({complaint.video_count}/{1})."

    return False, "Прикрепите фото или видео."

@router.message(ComplaintProcess.waiting_for_complaint_files)
async def process_media_group(message: Message, state: FSMContext):
    if not message.media_group_id:
        return

    user_id = message.from_user.id
    key = (user_id, str(message.media_group_id))
    _album_buffer[key].append(message)

    task = _album_tasks.get(key)
    if task and not task.done():
        task.cancel()

    async def delayed_flush():
        try:
            await asyncio.sleep(ALBUM_FLUSH_DELAY)
            await _flush_album(user_id, str(message.media_group_id), message.bot, message.chat.id)
        except asyncio.CancelledError:
            return

    _album_tasks[key] = asyncio.create_task(delayed_flush())

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
    if team_number not in TEAMS:
        await message.answer("Такой команды нет. Введите номер команды еще раз.")
        return
    registration[user_id].team_number = team_number
    await add_user(registration[user_id])

    active_sessions[user_id] = registration[user_id]
    del registration[user_id]

    await message.answer("Регистрация завершена! Спасибо.")
    await message.answer("Главное меню.", reply_markup=get_main_menu_student_keyboard())
    await state.set_state(MainMenu.main_menu)

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
                await state.set_state(MainMenu.main_menu_student)
            case "Организатор":
                await message.answer("Главное меню.", reply_markup=get_main_menu_organizer_keyboard())
                await state.set_state(MainMenu.main_menu_organizer)
            case "РПГ-организаторы":
                await message.answer("Главное меню.", reply_markup=get_main_menu_rpg_organizer_keyboard())
                await state.set_state(MainMenu.main_menu_rpg_organizer)
            case "Администраторы по комнатам":
                await message.answer("Главное меню.", reply_markup=get_main_menu_admins_keyboard())
                await state.set_state(MainMenu.main_menu_admins)
            case "Команда рейтинга":
                await message.answer("Главное меню.", reply_markup=get_main_menu_rating_team_keyboard())
                await state.set_state(MainMenu.main_menu_rating_team)
            case "Команда медиа":
                await message.answer("Главное меню.", reply_markup=get_main_menu_media_team_keyboard())
                await state.set_state(MainMenu.main_menu_media_team)
            case "Главный организатор":
                await message.answer("Главное меню.", reply_markup=get_main_menu_chief_organizer_keyboard())
                await state.set_state(MainMenu.main_menu_chief_organizer)

async def send_files(bot: Bot, complaint_id: int, tg_id: int = None) -> str:
    complaint = await get_complaint(complaint_id)
    if not complaint:
        return "Жалоба не найдена."

    user_id = tg_id
    files = await get_files_by_complaint(complaint_id)
    if not files:
        return "Файлов в жалобе нет."
    
    for file in files:
        try:
            if 'image' in file.mime_type:
                await bot.send_photo(chat_id=user_id, photo=file.tg_file_id, caption=f"Файл из жалобы: {file.file_name}")
            elif 'video' in file.mime_type:
                await bot.send_video(chat_id=user_id, video=file.tg_file_id, caption=f"Файл из жалобы: {file.file_name}")
            else:
                await bot.send_document(chat_id=user_id, document=file.tg_file_id, caption=f"Файл из жалобы: {file.file_name}")
        except Exception as e:
            print(f"Error sending file {file.file_id}: {e}")
    return f"Файлы отправлены пользователю {user_id}."

async def show_main_menu(bot: Bot, user_id: int, state: FSMContext):
    match active_sessions[user_id].role:
            case "Участник":
                await bot.send_message(chat_id=user_id, text="Главное меню.", reply_markup=get_main_menu_student_keyboard())
                await state.set_state(MainMenu.main_menu_student)
            case "Организатор":
                await bot.send_message(chat_id=user_id, text="Главное меню.", reply_markup=get_main_menu_organizer_keyboard())
                await state.set_state(MainMenu.main_menu_organizer)
            case "РПГ-организаторы":
                await bot.send_message(chat_id=user_id, text="Главное меню.", reply_markup=get_main_menu_rpg_organizer_keyboard())
                await state.set_state(MainMenu.main_menu_rpg_organizer)
            case "Администраторы по комнатам":
                await bot.send_message(chat_id=user_id, text="Главное меню.", reply_markup=get_main_menu_admins_keyboard())
                await state.set_state(MainMenu.main_menu_admins)
            case "Команда рейтинга":
                await bot.send_message(chat_id=user_id, text="Главное меню.", reply_markup=get_main_menu_rating_team_keyboard())
                await state.set_state(MainMenu.main_menu_rating_team)
            case "Команда медиа":
                await bot.send_message(chat_id=user_id, text="Главное меню.", reply_markup=get_main_menu_media_team_keyboard())
                await state.set_state(MainMenu.main_menu_media_team)
            case "Главный организатор":
                await bot.send_message(chat_id=user_id, text="Главное меню.", reply_markup=get_main_menu_chief_organizer_keyboard())
                await state.set_state(MainMenu.main_menu_chief_organizer)

async def main():
    global bot_instance
    bot_instance = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start_handler, CommandStart())
    dp.include_router(router)

    await load_datastore()
    await dp.start_polling(bot_instance)

if __name__ == "__main__":
    asyncio.run(main())
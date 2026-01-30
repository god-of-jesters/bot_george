import asyncio
import os
import csv
from dotenv import load_dotenv
from collections import defaultdict

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from database import load_datastore, USERS, TEAMS, FILES, COMPLAINTS, PRODUCT_NAME_INDEX, PRODUCTS
from repo.team_repo import *
from repo.user_repo import *
from repo.file_repo import *
from repo.complaint_repo import *
from repo.message_repo import Message as ms
from repo.message_repo import add_message, delete_message, update_message, get_message
from entityes.sequence import *
from entityes.logger import *

from keyboards import *
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()
API_TOKEN = os.getenv("BOT")
active_sessions = {}
registration = {}
complaintes = {}
alarm : dict[int: dict[int, int]] = {}
process_al = {}
al = {}
edit_users = {}
special_step = {}
violetion_vines = {
    "Нахождение на базе без личной карточки участника": 10,
    "Нахождение в неподходящей под погодные условия одежде на улице": 7,
    "Употребление никотиносодержащей продукции в неположенном месте": 15,
    "Нецензурная речь": 15,
    "Провоз и употребление энергетических напитков": 10,
    "Нахождение после отбоя участника вне своей комнаты": 20,
    "Нарушение общественного спокойствия после отбоя": 25,
    "Пропуск программных моментов без уважительной причины": 20,
    "Порча имущества базы/организаторов/участников": 30,
    "Кража": 50,
    "Оскорбления/конфликты на почве розни": 50,
    "Опьянение": 50,
}
_album_buffer: dict[tuple[int, str], list[Message]] = defaultdict(list)
_album_tasks: dict[tuple[int, str], asyncio.Task] = {}

MAX_PHOTOS = 3
MAX_VIDEOS = 1
ALBUM_FLUSH_DELAY = 0.7
router = Router()

async def _apply_complaint_decision(bot: Bot, reviewer_id: int, com: "Complaint", decision: str):
    adr_user = await get_user(com.adresat)
    fine = violetion_vines.get(com.violetion, 0)

    if decision == "yes":
        if adr_user.role == "Участник":
            adr_user.reiting -= fine
            await update_user(adr_user)
            await bot.send_message(
                adr_user.user_id,
                f"На вас пришла новая жалоба. Снято {fine} единиц рейтинга.\n"
                f"Время жалобы: {com.date_created}.\n"
                f"Описание: {com.description}"
            )
            com.execution = "done"
    else:
        await bot.send_message(
            adr_user.user_id,  
            "На вас была подана жалоба. Команда рейтинга посчитала, что жалоба недействительна."
        )
        com.execution = "rejected"

    await update_complaint(com)

    # Notify the user who filed the complaint after it was processed
    verdict_text = "удовлетворена" if decision == "yes" else "не удовлетворена"
    try:
        await bot.send_message(
            com.user_id,
            "Ваша жалоба обработана.\n"
            f"Нарушение: {getattr(com, 'violetion', '—')}\n"
            f"Описание: {getattr(com, 'description', '—')}\n"
            f"Решение: {verdict_text}"
        )
    except Exception:
        # If user blocked the bot / chat unavailable, don't break the reviewer flow
        pass

@router.callback_query(lambda c: c.data in ("yes", "no"), ComplaintReview.main)
async def process_complaint_from_main(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = callback_query.from_user.id

    com = al.get(user_id)
    if not com:
        await callback_query.message.answer("Текущая жалоба не найдена.")
        await show_main_menu(callback_query.bot, user_id, state)
        return

    await _apply_complaint_decision(callback_query.bot, user_id, com, callback_query.data)
    al.pop(user_id, None)

    if callback_query.data == "yes":
        await callback_query.answer("Успешно сняли рейтинг")
    else:
        await callback_query.answer("Успешно защитили человека")

    await show_main_menu(callback_query.bot, user_id, state)

@router.callback_query(lambda c: c.data in ("yes", "no"), ComplaintReview.stat)
async def process_complaint_fate(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = callback_query.from_user.id

    com = al.get(user_id)
    if not com:
        await callback_query.message.answer("Текущая жалоба не найдена.")
        await show_main_menu(callback_query.bot, user_id, state)
        return

    await _apply_complaint_decision(callback_query.bot, user_id, com, callback_query.data)
    al.pop(user_id, None)

    other = await get_oldest_complaint()
    if other and other.status == "alert":
        await callback_query.message.answer(
            "Жалоба успешно обработана. Есть еще срочные жалобы, ответить?",
            reply_markup=get_yes_no_keyboard()
        )
        await state.set_state(ComplaintReview.safe)
        return

    await callback_query.message.answer("Жалоба успешно обработана.")
    await show_main_menu(callback_query.bot, user_id, state)

@router.callback_query(lambda c: c.data in ("yes", "no"))
async def process_alarm_complaint(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = callback_query.from_user.id

    if callback_query.data == "no":
        await callback_query.message.answer("Скип скип")
        await show_main_menu(callback_query.bot, user_id, state)
        return

    queue = alarm.get(user_id, [])
    if not queue:
        await callback_query.message.answer("Срочных жалоб сейчас нет.")
        await show_main_menu(callback_query.bot, user_id, state)
        return

    com = None
    while queue:
        cid = queue[0]
        cand = await get_complaint(cid)

        if cand and cand.execution == "new" and cand.status == "alert":
            com = cand
            queue.pop(0)
            break
        else:
            queue.pop(0)

    if not com:
        await callback_query.message.answer("Срочных жалоб сейчас нет.")
        await show_main_menu(callback_query.bot, user_id, state)
        return

    process_al.setdefault(user_id, []).append(com.complaint_id)
    await update_execution(com.complaint_id, "view")

    user = await get_user(com.user_id)
    adr = await get_user(com.adresat)

    await send_complaint_files(callback_query.bot, user_id, com.complaint_id)
    await callback_query.message.answer(
        f"Жалоба от {user.fio}\nНа {adr.fio}\nЖалоба: {com.description}",
        reply_markup=get_yes_no_keyboard()
    )

    al[user_id] = com
    await state.set_state(ComplaintReview.stat)

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

@router.message(Command("teg"))
async def cmd_teg(message: Message):
    id = message.from_user.id
    await message.answer(f"{id}")

"""MAIN MENUS"""

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
        case "my_complaints":
            s = ''
            complaints = await get_user_complaints(user_id)
            for i, com in enumerate(complaintes):
                s += str(i) + '.\n'
                s += 'На: ' + com.adresat + '\n'
                s += com.description
            await callback_query.message.answer()
        case "entertainment":
            await state.set_state(MainMenu.student_entertainment)
            await callback_query.message.answer("Развлечения.", reply_markup=get_student_entertainment_keyboard())
        case "help":
            await callback_query.message.answer("Помощь.", reply_markup=get_student_help_keyboard())
            await state.set_state(MainMenu.student_help)
        case "message_to_admin":
            await callback_query.message.answer("Напишите ваше сообщение администрации.")
            await state.set_state(MainMenu.message_to_admin)
        case _:
            await callback_query.message.answer("Команда не распознана.")

@router.callback_query(MainMenu.main_menu_organizer)
async def show_main_organizer(callback_query: CallbackQuery, state: FSMContext):
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
            await callback_query.message.answer("Напишите сообщение для команды рейтинга.")
            await state.set_state(MainMenu.message_to_rating_team)

        case "mailing":
            await callback_query.message.answer("Введите текст рассылки.\n")
            await state.set_state(Mailing.waiting_for_mailing_text)

        case "help":
            await callback_query.message.answer("Помощь.\n(Здесь будет справка для организаторов.)")

        case _:
            await callback_query.message.answer("Команда не распознана.")

@router.callback_query(MainMenu.main_menu_rpg_organizer)
async def show_main_rpg_organizer(callback_query: Message, state: FSMContext):
    user_id = callback_query.from_user.id
    data = callback_query.data
    role = getattr(active_sessions.get(user_id), "role", None)
    if role != "РПГ-организаторы":
        return

    match data:
        case "profile":
            await callback_query.message.answer("Профиль РПГ-организатора.", reply_markup=get_profile_keyboard())
            await state.set_state(MainMenu.profile)

        case "entertainment":
            await callback_query.message.answer("Магазин.\n(Здесь будет магазин для РПГ-организаторов.)")

        case "operations_with_participants":
            await callback_query.message.answer("Операции с участниками.\n(Здесь будут операции с участниками.)")

        case "operation_history":
            await callback_query.message.answer("История операций.\n(Здесь будет история операций.)")

        case "mailing":
            await callback_query.message.answer("Введите текст рассылки.\n")
            await state.set_state(Mailing.waiting_for_mailing_text)

        case "contact":
            await callback_query.message.answer("Напишите сообщение для команды рейтинга.")
            await state.set_state(MainMenu.message_to_rating_team)

        case "help":
            await callback_query.message.answer("Помощь.\n(Здесь будет справка для РПГ-организаторов.)")

        case _:
            await callback_query.message.answer("Команда не распознана.")

@router.callback_query(MainMenu.main_menu_admins)
async def show_main_admins(callback_query: Message, state: FSMContext):
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
            await callback_query.message.answer("Комнатные обращения", reply_markup=get_room_admins_complaints())

        case "mailing":
            await callback_query.message.answer("Введите текст рассылки.\n")
            await state.set_state(Mailing.waiting_for_mailing_text)

        case "activity_log":
            await callback_query.message.answer("Журнал действий.\n(Здесь будет журнал действий.)")

        case "contact":
            await callback_query.message.answer("Напишите сообщение для команды рейтинга.")
            await state.set_state(MainMenu.message_to_rating_team)

        case "help":
            await callback_query.message.answer("Помощь.\n(Здесь будет справка для администраторов по комнатам.)")

        case _:
            await callback_query.message.answer("Команда не распознана.")

@router.callback_query(MainMenu.main_menu_rating_team)
async def show_main_rating_team(callback_query: CallbackQuery, state: FSMContext):
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
            complaint = await get_oldest_complaint()
            if complaint:
                al[user_id] = complaint
                await send_complaint_files(callback_query.bot, user_id, complaint.complaint_id)
                await callback_query.message.answer(f"Статус: {complaint.status}\nДата создания: {complaint.date_created}\nЖалоба: {complaint.description}\n \
                                                    Тип жалобы: {complaint.violetion}", reply_markup=get_yes_no_keyboard())
                await state.set_state(ComplaintReview.main)
            else:
                await callback_query.message.answer(f'Пока что нет жалоб.')
                await state.set_state(MainMenu.main_menu_rating_team)
                await show_main_menu(callback_query.bot, user_id, state)

        case "participants":
            mes = await get_roles_stats_message()
            await callback_query.message.answer(mes, reply_markup=get_users_keyboard())
            await state.set_state(MainMenu.users)

        case "assign_rating":
            await callback_query.message.answer("Начисление и штрафы.\n")

        case "inbox_messages":
            await callback_query.message.answer("Входящие сообщения.\n")

        case "mailing":
            await callback_query.message.answer("Введите текст рассылки.\n")
            await state.set_state(Mailing.waiting_for_mailing_text)

        case "security":
            await callback_query.message.answer("Безопастность.\n(Здесь будет модуль безопасности.)")

        case "help":
            await callback_query.message.answer("Помощь.\n(Здесь будет справка для команды рейтинга.)")

        case _:
            await callback_query.message.answer("Команда не распознана.")

@router.callback_query(MainMenu.main_menu_chief_organizer)
async def show_main_chief_organizer(callback_query: Message, state: FSMContext):
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

"""STUDENT MENU"""

@router.callback_query(MainMenu.student_entertainment)
async def show_student_entertainment(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    data = callback_query.data
    role = getattr(active_sessions.get(user_id), "role", None)
    if role != "Участник":
        return
    match data:
        case "shop":
            await callback_query.message.answer("Магазин.", reply_markup=get_student_shop_keyboard())
        case "tasks":
            await callback_query.message.answer("Задания.", reply_markup=get_student_tasks_keyboard())
        case "zags":
            await callback_query.message.answer("ЗАГС.", reply_markup=get_student_zags_keyboard())
        case "back_to_main_menu":
            await show_main_menu(callback_query.bot, user_id, state)
        case _:
            await callback_query.message.answer("Команда не распознана.")

@router.callback_query(MainMenu.student_help)
async def show_student_help(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    data = callback_query.data
    role = getattr(active_sessions.get(user_id), "role", None)
    if role != "Участник":
        return
    match data:
        case "rules":
            await callback_query.message.answer("Правила и обязанности участника.")
        case "help_in_work":
            await callback_query.message.answer("Помощь по работе с ботом.")
        case _:
            await callback_query.message.answer("Команда не распознана.")
    await show_main_menu(callback_query.bot, user_id, state)

@router.message(MainMenu.message_to_admin)
async def process_message_to_admin(message: Message, state: FSMContext):
    user_id = message.from_user.id
    message_text = message.text
    await add_message(
        ms(
            user_id=user_id,
            adresat="Администраторы по комнатам",
            badge_number=0,
            text=message_text,
        )
    )
    await message.answer("Ваше сообщение отправлено администрации. Спасибо.")
    await show_main_menu(message.bot, user_id, state)

@router.message(MainMenu.message_to_rating_team)
async def process_message_to_rating_team(message: Message, state: FSMContext):
    user_id = message.from_user.id
    role = getattr(active_sessions.get(user_id), "role", None)
    if role != "Администраторы по комнатам":
        await show_main_menu(message.bot, user_id, state)
        return
    message_text = message.text
    await add_message(
        ms(
            user_id=user_id,
            adresat="Команда рейтинга",
            badge_number=0,
            text=message_text,
        )
    )
    await message.answer("Ваше сообщение отправлено команде рейтинга. Спасибо.")
    await show_main_menu(message.bot, user_id, state)

"""COMPLAINTS"""

@router.callback_query(lambda c: c.data == "complaint_done", ComplaintProcess.waiting_for_complaint_files)
async def finish_complaint_cb(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.answer()
    complaint = complaintes[user_id]
    complaint_id = await add_complaint(complaint)
    await log_complaint_created(complaint.user_id, complaint.adresat, complaint_id)


    if complaint.status == "alert":
            await notify_all_reiting_team(callback.message.bot, complaintes[user_id], state)

    if user_id in complaintes:
        del complaintes[user_id]

    await callback.message.answer("Жалоба отправлена. Спасибо.")
    await show_main_menu(callback.bot, user_id, state)

@router.callback_query(MainMenu.complaint)
async def process_complaint_callback(callback_query: Message, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    if user_id not in complaintes:
        complaintes[user_id] = Complaint(user_id=user_id, status="Новая")
    await callback_query.message.answer("Введите номер бейджа.")
    await state.set_state(ComplaintProcess.waiting_for_badge)

@router.message(ComplaintProcess.waiting_for_badge)
async def process_complaint_badge(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not message.text.isdigit():
        await message.answer("Номер должен быть числом, введите еще раз")
        return
    num = int(message.text)
    user = await get_user_by_badge(num)
    if user:
        if num == active_sessions[user_id].badge_number:
            await message.answer('Нельзя подать жалобу на себя же. Введите еще раз номер бейджа')
            await state.set_state(ComplaintProcess.waiting_for_badge)
            return
        complaintes[user_id].adresat = user.user_id
        
        await message.answer(text="Выберете категорию жалобы.", reply_markup=get_complaint_category_keyboard())
        await state.set_state(ComplaintProcess.waiting_for_complaint_category)
    else:
        await message.answer('Такого человека не существует, введите номер бейджа еще раз')
        return

@router.callback_query(ComplaintProcess.waiting_for_complaint_category)
async def process_complaint_category_callback(callback_query: Message, state: FSMContext):
    text_alert = "Выберете тип нарушения \n\
    1. Провоз и употребление энергитических напитков \n\
    2. Нахождение после отбоя участника вне своей комнаты \n\
    3. Нарушение общественного спокойствия после отбоя \n\
    4. Порча имущества базы/организаторов/участников \n\
    5. Кража \n\
    6. Опьянение"

    text_soon = 'Выберете тип нарушения \n\
    1. Нахождение на базе без личной карточки участника \n\
    2. Нахождение в неподходящей под погодные условия одежде на улице \n\
    3. Употребление никотиносодержащей продукции в неположенном месте \n\
    4. Нецензурная речь\n'

    text_other = """
    Выберете тип нарушения
    1. Пропуск программных моментов без уважительной причины
    2. Оскорбления/конфликты на почве розни
    """
    data = callback_query.data
    user_id = callback_query.from_user.id
    if user_id in complaintes:
        complaintes[user_id].status = data
        match data:
            case 'alert':
                await callback_query.bot.send_message(user_id, text_alert, reply_markup=get_alert_keyboard())
            case 'soon':
                await callback_query.bot.send_message(user_id, text_soon, reply_markup=get_soon_keyboard())
            case 'room_problems':
                await callback_query.bot.send_message(user_id, 'Опишите вашу проблему', reply_markup=get_soon_keyboard())
                await state.set_state(ComplaintProcess.waiting_for_complaint_text)
                return
            case _:
                await callback_query.bot.send_message(user_id, text_other, reply_markup=get_other_keyboard())
        await state.set_state(ComplaintProcess.waiting_for_violation_type)

@router.callback_query(ComplaintProcess.waiting_for_violation_type)
async def process_complaint_violation_type(callback_query: CallbackQuery, state: FSMContext):
    data = int(callback_query.data)
    user_id = callback_query.from_user.id
    c1 = {
        1: 'Провоз и употребление энергитических напитков',
        2: 'Нахождение после отбоя участника вне своей комнаты',
        3: 'Нарушение общественного спокойствия после отбоя',
        4: 'Порча имущества базы/организаторов/участников',
        5: 'Кража',
        6: 'Опьянение'
    }
    c2 = {
        1: 'Нахождение на базе без личной карточки участника',
        2: 'Нахождение в неподходящей под погодные условия одежде на улице',
        3: 'Употребление никотиносодержащей продукции в неположенном месте',
        4: 'Нецензурная речь'
    }
    c3 = {
        1: 'Пропуск программных моментов без уважительной причины',
        2: 'Оскорбления/конфликты на почве розни'
    }
    match complaintes[user_id].status:
        case 'alert':
            complaintes[user_id].violetion = c1[data]
        case 'soon':
            complaintes[user_id].violetion = c2[data]
        case _:
            complaintes[user_id].violetion = c3[data]

    await callback_query.message.answer("Опишите вашу жалобу подробно.")
    await state.set_state(ComplaintProcess.waiting_for_complaint_text)

@router.message(ComplaintProcess.waiting_for_complaint_text)
async def process_complaint_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    teg = message.from_user.username
    if user_id in complaintes:
        complaintes[user_id].description = teg + '\n' + message.text
        await message.answer("При наличии доказательств, прикрепите их в следующем сообщении. Отправьте фото или видео, или /skip чтобы завершить без файлов.")
        await state.set_state(ComplaintProcess.waiting_for_complaint_files)

@router.message(Command("skip"), ComplaintProcess.waiting_for_complaint_files)
async def skip_files(message: Message, state: FSMContext):
    user_id = message.from_user.id
    complaint = complaintes.get(user_id)
    if not complaint:
        await message.answer("Жалоба не найдена. Начните заново.")
        return

    complaint_id = await add_complaint(complaint)
    await log_complaint_created(complaint.user_id, complaint.adresat, complaint_id)

    if getattr(complaint, "status", None) == "alert":
        await notify_all_reiting_team(message.bot, complaint, state)

    complaintes.pop(user_id, None)

    await message.answer("Жалоба отправлена. Спасибо.")
    await show_main_menu(message.bot, user_id, state)

async def _finalize_complaint(bot: Bot, user_id: int, state: FSMContext, chat_id: int):
    complaint = complaintes.get(user_id)
    if not complaint:
        await bot.send_message(chat_id, "Жалоба не найдена. Начните заново.")
        return

    complaint_id = await add_complaint(complaint)
    await log_complaint_created(complaint.user_id, complaint.adresat, complaint_id)
    await link_files_to_complaint(complaint_id, complaint.files)

    if getattr(complaint, "status", None) == "alert":
        await notify_all_reiting_team(bot, complaint, state)

    complaintes.pop(user_id, None)

    await bot.send_message(chat_id, "Жалоба отправлена. Спасибо.")
    await show_main_menu(bot, user_id, state)

async def add_media_to_current_complaint(message: Message, complaint: Complaint):
    saved = 0

    if message.photo:
        if complaint.photo_count < MAX_PHOTOS:
            photo = message.photo[-1]
            file = File(
                id=None,
                tg_id=complaint.user_id,
                tg_file_id=photo.file_id,
                complaint_id=None,
                file_name=f"photo_{complaint.photo_count + 1}.jpg",
                mime_type="image/jpeg",
                file_size=photo.file_size
            )
            file_row_id = await add_file(file)
            file.id = file_row_id
            await log_file_attached(complaint.user_id, file.id, file.tg_file_id)
            complaint.files.append(file.id)
            await log_file_attached(complaint.user_id, file.id, file.tg_file_id)
            complaint.photo_count += 1
            saved += 1

    if message.video:
        if complaint.video_count < MAX_VIDEOS:
            video = message.video
            file = File(
                id=None,
                tg_id=complaint.user_id,
                tg_file_id=video.file_id,
                complaint_id=None,
                file_name=video.file_name or f"video_{complaint.video_count + 1}.mp4",
                mime_type=video.mime_type or "video/mp4",
                file_size=video.file_size
            )
            file_row_id = await add_file(file)
            file.id = file_row_id
            await log_file_attached(complaint.user_id, file.id, file.tg_file_id)
            complaint.files.append(file.id)
            await log_file_attached(complaint.user_id, file.id, file.tg_file_id)
            complaint.video_count += 1
            saved += 1

    if saved == 0:
        return 0, "Прикрепите фото или видео."
    return saved, f"Доказательства приняты: +{saved}."

async def flush_album(user_id: int, media_group_id: str, bot: Bot, chat_id: int, state: FSMContext):
    key = (user_id, media_group_id)
    msgs = _album_buffer.pop(key, [])
    _album_tasks.pop(key, None)

    if not msgs:
        return

    complaint = complaintes.get(user_id)
    if not complaint:
        await bot.send_message(chat_id, "Жалоба не найдена. Начните заново.")
        return

    results = []
    for msg in sorted(msgs, key=lambda m: m.message_id):
        _, text = await add_media_to_current_complaint(msg, complaint)
        results.append(text)

    await bot.send_message(chat_id, "Файлы обработаны:\n" + "\n".join("• " + r for r in results))
    await _finalize_complaint(bot, user_id, state, chat_id)

@router.message(ComplaintProcess.waiting_for_complaint_files)
async def handle_files(message: Message, state: FSMContext):
    user_id = message.from_user.id
    complaint = complaintes.get(user_id)
    if not complaint:
        await message.answer("Жалоба не найдена. Начните заново.")
        return

    if message.media_group_id:
        mgid = str(message.media_group_id)
        key = (user_id, mgid)
        _album_buffer[key].append(message)

        task = _album_tasks.get(key)
        if task and not task.done():
            task.cancel()

        async def delayed():
            try:
                await asyncio.sleep(ALBUM_FLUSH_DELAY)
                await flush_album(user_id, mgid, message.bot, message.chat.id, state)
            except asyncio.CancelledError:
                return
            except Exception as e:
                await message.bot.send_message(message.chat.id, f"Ошибка обработки альбома: {e}")

        _album_tasks[key] = asyncio.create_task(delayed())
        return

    saved, text = await add_media_to_current_complaint(message, complaint)
    if saved == 0:
        await message.answer(text)
        return

    await message.answer("Файлы обработаны. " + text)
    await _finalize_complaint(message.bot, user_id, state, message.chat.id)

@router.callback_query(lambda c: c.data == 'agree' or c.data == 'disagree')
async def process_complaint_student(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if callback_query.data == 'agree':
        active_sessions[user_id].reiting -= violetion_vines[special_step[user_id].violetion]
        await update_user(active_sessions[user_id])
        await callback_query.message.answer(f'С вас сняли {violetion_vines[special_step[user_id].violetion]} очков рейтинга.')
        await show_main_menu(callback_query.bot, user_id, state)
    else:
        await callback_query.message.answer('Ваша жалоба отослана на рассмотрение команде рейтинга.')
        await show_main_menu(callback_query.bot, user_id, state)



"""USERS"""

@router.callback_query(MainMenu.users)
async def process_users_callback(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    match data:
        case 'all_users':
            users = await get_all_users()
            mes = "Список всех пользователей:\n"
            i = 0
            for user in users:
                if i == 39:
                    mes += f"Бейдж: {user.badge_number}, ФИО: {user.fio}, Роль: {user.role}\n"
                    await callback_query.bot.send_message(chat_id=user_id, text=mes, reply_markup=get_users_keyboard())
                    mes = ''
                    i = 0
                else:
                    mes += f"Бейдж: {user.badge_number}, ФИО: {user.fio}, Роль: {user.role}\n"
                    i += 1
            await callback_query.message.answer(mes, reply_markup=get_users_keyboard())
        case 'edit_user_data':
            await callback_query.message.answer('Введите номер бейджа пользователя, данные которого хотите изменить.')
            await state.set_state(UserDataEdit.waiting_for_badge_number)
        case _:
            users = await get_all_users()
            mes = "Список всех пользователей:\n"
            i = 0
            for user in users:
                if i == 39:
                    mes += f"Бейдж: {user.badge_number}, ФИО: {user.fio}, Роль: {user.role}\n"
                    await callback_query.bot.send_message(chat_id=user_id, text=mes, reply_markup=get_users_keyboard())
                    mes = ''
                    i = 0
                else:
                    mes += f"Бейдж: {user.badge_number}, ФИО: {user.fio}, Роль: {user.role}\n"
                    i += 1
            await callback_query.message.answer(mes, reply_markup=get_users_keyboard())

@router.message(UserDataEdit.waiting_for_badge_number)
async def process_user_data_badge(message: Message, state: FSMContext): 
    user_id = message.from_user.id
    if not message.text.isdigit():
        await message.answer("Номер должен быть числом, введите еще раз")
        return
    num = int(message.text)
    user = await get_user_by_badge(num)
    if user:
        if user.user_id == user_id:
            await message.answer("Вы не можете изменить данные самого себя.")
            return
        if user.role == "Главный организатор" or user.role == 'Команда рейтинга':
            await message.answer("Вы не можете изменить данные этого пользователя.")
            return
        edit_users[user_id] = user
        await message.answer(f"Выбран пользователь: {user.fio}. Выберете что будем изменять.", reply_markup=get_edit_badge_keyboard())
        await state.set_state(UserDataEdit.waiting_for_change_choice)
    else:
        await message.answer('Такого человека не существует, введите номер бейджа еще раз')
        return

@router.callback_query(UserDataEdit.waiting_for_change_choice)
async def process_user_data_change(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    data = callback_query.data
    match data:
        case 'fio':
            await state.update_data(field_to_change='fio')
            await callback_query.message.answer('Введите новое ФИО, все с большой буквы в именительном падеже.')
            await state.set_state(UserDataEdit.waiting_for_new_value)
        case 'team_number':
            await state.update_data(field_to_change='team_number')
            await callback_query.message.answer('Введите новую команду (номер).')
            await state.set_state(UserDataEdit.waiting_for_new_value)
        case 'role':
            await state.update_data(field_to_change='role')
            await callback_query.message.answer('Введите новую роль.')
            await state.set_state(UserDataEdit.waiting_for_new_value)
        case 'badge_number':
            await state.update_data(field_to_change='badge_number')
            await callback_query.message.answer('Введите новый номер бейджа.')
            await state.set_state(UserDataEdit.waiting_for_new_value)
        case 'reiting':
            await state.update_data(field_to_change='reiting')
            await callback_query.message.answer('Введите новое количество очков рейтинга.')
            await state.set_state(UserDataEdit.waiting_for_new_value)
        case 'balance':
            await state.update_data(field_to_change='balance')
            await callback_query.message.answer('Введите новое количество очков баланса.')
            await state.set_state(UserDataEdit.waiting_for_new_value)
        case 'edit_user_back':
            await callback_query.message.answer('Вы вернулись в меню изменения данных пользователя.')
            await show_main_menu(callback_query.bot, user_id, state)
        case _:
            await callback_query.message.answer('Неверный выбор, выберете что будем изменять.')
            await state.set_state(UserDataEdit.waiting_for_change_choice) 

@router.message(UserDataEdit.waiting_for_new_value)
async def process_user_new_value(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = edit_users.get(user_id)

    if not user:
        await message.answer("Пользователь для редактирования не найден, начните заново.")
        await show_main_menu(message.bot, user_id, state)
        return

    data = await state.get_data()
    field = data.get("field_to_change")
    value = message.text.strip()

    match field:
        case "fio":
            user.fio = value
        case "team_number":
            if not value.isdigit():
                await message.answer("Номер команды должен быть числом, введите еще раз.")
                return
            if int(value) >= 10 or int(value) <= 0:
                await message.answer("Номер команды должен быть от 1 до 9, введите еще раз.")
                return
            user.team_number = int(value)
        case "role":
            if value.lower() not in ["участник", "организатор", "рпг-организатор", "администратор по комнатам", "команда рейтинга", "команда медиа", "главный организатор"]:
                await message.answer("Неверная роль, введите еще раз.")
                return
            user.role = value
        case "badge_number":
            if 'ком' in value.lower() and len(value) <= 6:
                if value[3:].isdigit():
                    user.badge_number = int(value[3:])
                else:
                    await message.answer("Номер бейджа должен быть числом, введите еще раз.")
                    return
            elif int(value) > 10 or int(value) < 1000:
                user.badge_number = int(value[3:])
            else:
                await message.answer("Неверный формат ввода. Введите данные в виде 'ком123' или число от 10 до 1000.")
                return
        case "reiting":
            if not value.isdigit():
                await message.answer("Рейтинг должен быть числом, введите еще раз.")
                return
            if int(value) < 0 or int(value) > 1000:
                await message.answer("Рейтинг не может быть отрицательным, введите еще раз.")
                return
            user.reiting = int(value)
        case "balance":
            if not value.isdigit():
                await message.answer("Баланс должен быть числом, введите еще раз.")
                return
            if int(value) < 0:
                await message.answer("Баланс не может быть отрицательным, введите еще раз.")
                return
            user.balance = int(value)
        case _:
            await message.answer("Неизвестное поле для изменения, начните заново.")
            await show_main_menu(message.bot, user_id, state)
            return

    await update_user(user)
    active_sessions[user.user_id] = user

    await message.answer("Данные пользователя обновлены.")
    await show_main_menu(message.bot, user_id, state)

"""REGISTRATION"""

@router.message(Reg.waiting_for_bage_number)
async def process_badge_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text.isdigit():
        badge_number = int(message.text)
        existing_user = await get_user_by_badge(badge_number)
        if not existing_user:
            await message.answer("Такого пользователя нет. Введите номер бейджа еще раз.")
            return
    elif 'ком' in message.text.lower() and len(message.text) <= 6:
        if message.text[3:].isdigit():
            badge_number = int(message.text[3:])
            existing_user = await get_user_by_badge(badge_number)
            if not existing_user:
                await message.answer("Такого пользователя нет. Введите номер бейджа еще раз.")
                return
    else:
        await message.answer('Неверный формат ввода. Введите данные в виде')
    registration[user_id].badge_number = badge_number

    await message.answer("Введите ФИО, все с большой буквы в именительном падеже.")
    await state.set_state(Reg.waiting_for_fio)

@router.message(Reg.waiting_for_fio)
async def process_fio(message: Message, state: FSMContext):
    user_id = message.from_user.id
    registration[user_id].fio = message.text.strip()
    existing_user = await get_user_by_badge(registration[user_id].badge_number)
    if existing_user != registration[user_id]:
        await message.answer("Такого пользователя не существует, проверьте введеные данные. Пришлите номер бейджа")
        await state.set_state(Reg.waiting_for_bage_number)
        return
    existing_user.user_id = user_id
    if existing_user.user_id != user_id:
        await update_user(existing_user) 
    
    active_sessions[user_id] = existing_user
    del registration[user_id]

    await message.answer("Регистрация завершена! Спасибо.")
    await add_active(user_id, active_sessions[user_id].role)
    await show_main_menu(message.bot, user_id, state)

"""MAILING"""

@router.message(Mailing.waiting_for_mailing_text)
async def handle_mailing_text(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    role = active_sessions[user_id].role
    user = await get_user(user_id)
    if not await get_permission_maling(user.badge_number):
        message.answer('Нет доступа к рассылке')
        await show_main_menu(bot, user_id, state)
        return

    if role == 'Команда рейтинга':
        text = 'Общая рассылка от команды рейтинга\n\n'
    elif role == 'Организатор':
        text = 'Общая рассылка от организаторов'
    elif role == 'Администраторы по комнатам':
        text = 'Общая рассылка от организаторов'
    elif role == 'РПГ-организаторы':
        text = 'Общая рассылка от РПГ-организаторов'
    
    text = text + (message.text or "").strip()
    if role == 'Администраторы по комнатам':
        recipients = await get_participants_and_room_admins_tg_ids(exclude_tg_id=user_id)
    else:
        recipients = await get_participants_tg_ids(exclude_tg_id=user_id)

    sent = 0
    failed = 0

    for tg_id in recipients:
        try:
            await bot.send_message(tg_id, text)
            sent += 1
        except Exception:
            failed += 1

    await message.answer(f"Рассылка завершена. Отправлено: {sent}. Ошибок: {failed}.")
    await show_main_menu(message.bot, message.from_user.id, state)

"""UPLOAD REITING FILES"""

def _parse_int(v, default=0):
    try:
        if v is None:
            return default
        s = str(v).strip()
        if s == "":
            return default
        return int(float(s.replace(" ", "").replace(",", ".")))
    except Exception:
        return default

def _parse_text(v):
    if v is None:
        return ""
    return str(v).strip()

def _read_csv_rows(text: str, delimiter: str) -> list[list[str]]:
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    return [r for r in reader if any(str(x).strip() for x in r)]


def _rows_from_csv_bytes(data: bytes) -> list[dict]:
    text = data.decode("utf-8-sig", errors="replace")
    all_rows = _read_csv_rows(text, ";")
    if not all_rows:
        return []
    if all(len(r) <= 1 for r in all_rows) and "," in text:
        all_rows = _read_csv_rows(text, ",")

    header = [c.strip() for c in all_rows[0]]
    expected = ["badge_number", "full_name", "team_id", "daily_base", "penalties_sum", "bonuses_sum", "total_points", "updated_at"]

    has_header = False
    if len(header) >= 7:
        lower = [h.lower() for h in header]
        if all(x in lower for x in expected[:7]):
            has_header = True

    start_idx = 1 if has_header else 0
    rows = []

    for r in all_rows[start_idx:]:
        r = list(r) + [""] * (8 - len(r))
        badge_number = _parse_int(r[0], default=-1)
        if badge_number <= 0:
            continue

        updated_at = _parse_text(r[7]) or now_iso()

        rows.append(
            {
                "badge_number": badge_number,
                "full_name": _parse_text(r[1]),
                "team_id": _parse_int(r[2], default=None),
                "daily_base": _parse_int(r[3], default=100),
                "penalties_sum": _parse_int(r[4], default=0),
                "bonuses_sum": _parse_int(r[5], default=0),
                "total_points": _parse_int(r[6], default=0),
                "updated_at": updated_at,
            }
        )

    return rows

@router.message(Command("upload_reiting"))
async def upload_reiting_cmd(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    role = user.role
    if not role == 'Команда рейтинга':
        await message.answer("Доступно только для роли «команда рейтинга».")
        return
    await state.set_state(RatingCSV.waiting_for_csv)
    await message.answer("Пришли .csv файл с рейтингом (разделитель – запятая «;»).")


@router.message(RatingCSV.waiting_for_csv, F.document)
async def upload_reiting_file(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    role = user.role
    if not role == 'Команда рейтинга':
        await state.clear()
        await message.answer("Доступно только для роли «команда рейтинга».")
        return

    doc = message.document
    name = (doc.file_name or "").lower()
    if not name.endswith(".csv"):
        await message.answer("Нужен файл .csv.")
        return

    file = await message.bot.get_file(doc.file_id)
    data = await message.bot.download_file(file.file_path)
    content = data.read()

    rows = _rows_from_csv_bytes(content)
    if not rows:
        await message.answer("Не нашёл валидных строк. Проверь формат файла.")
        return

    n = await upsert_rating_rows(rows)
    await recalc_team_totals()
    await state.clear()
    await message.answer(f"Загружено строк: {n}.")


@router.message(RatingCSV.waiting_for_csv)
async def upload_reiting_wrong(message: Message):
    await message.answer("Пришли .csv файлом (документом).")


@router.message(Command("reiting"))
async def export_reiting(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys=ON;")
        cur = await db.execute(
            """
            SELECT badge_number, full_name, team_id, daily_base,
                   penalties_sum, bonuses_sum, total_points, updated_at
            FROM ratings
            ORDER BY team_id, total_points DESC, full_name
            """
        )
        rows = await cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(["badge_number", "full_name", "team_id", "daily_base", "penalties_sum", "bonuses_sum", "total_points", "updated_at"])
    for r in rows:
        writer.writerow(
            [
                r["badge_number"],
                r["full_name"],
                r["team_id"] if r["team_id"] is not None else "",
                r["daily_base"],
                r["penalties_sum"],
                r["bonuses_sum"],
                r["total_points"],
                r["updated_at"] or "",
            ]
        )

    filename = f"reiting_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = f"/tmp/{filename}"
    with open(path, "wb") as f:
        f.write(output.getvalue().encode("utf-8-sig"))

    await message.answer_document(FSInputFile(path, filename=filename))

async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    active = await get_active_users()
    if not active_sessions.get(user_id) and user_id not in active:
        registration[user_id] = User(user_id=user_id)
        await message.answer(
            "Приветствую! Для начала надо пройти регистрацию.\n"
            "Введите ваш номер бейджа.",
        )
        await state.set_state(Reg.waiting_for_bage_number)
    else:
        user = await get_user(user_id)
        await log_login(user.user_id, user.badge_number, user.role)
        active_sessions[user_id] = user
        await show_main_menu(message.bot, user_id, state=state)

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
            print(f"Error sending file {file.tg_file_id}: {e}")
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

async def send_complaint_files(bot: Bot, chat_id: int, complaint_id: int):
    rows = await get_files_by_complaint_id(complaint_id)

    if not rows:
        await bot.send_message(chat_id, "Файлы не прикреплены.")
        return

    for r in rows:
        tg_file_id = r["tg_file_id"]
        mime = (r["mime_type"] or "").lower()

        if mime.startswith("video"):
            await bot.send_video(chat_id, tg_file_id)
        else:
            # по умолчанию считаем фото
            await bot.send_photo(chat_id, tg_file_id)

async def notify_all_reiting_team(bot: Bot, complaint: Complaint, state: FSMContext):
    team = await get_raiting_team_tg()
    for member_id in team:
        await bot.send_message(
            member_id,
            "Пришла срочная жалоба! Ответить на неё?",
            reply_markup=get_yes_no_keyboard()
        )
        alarm.setdefault(member_id, [])
        alarm[member_id].append(complaint.complaint_id)

async def notify_persone(bot: Bot, complaint: "Complaint", state: FSMContext):
    fr = await get_user(complaint.user_id)

    if complaint.complaint_id:
        rows = await get_files_by_complaint_id(complaint.complaint_id)
        for r in rows:
            tg_file_id = r["tg_file_id"]
            mime = (r["mime_type"] or "").lower()
            if mime.startswith("video"):
                await bot.send_video(complaint.adresat, tg_file_id)
            else:
                await bot.send_photo(complaint.adresat, tg_file_id)

    fine = violetion_vines.get(complaint.violetion, 0)
    adr = await get_user_by_badge(complaint.adresat)

    if fr.badge_number < 100:
        await bot.send_message(
            complaint.adresat,
            "На вас пришла новая жалоба от организатора.\n"
            f"Снято {fine} единиц рейтинга.\n"
            f"Время жалобы: {complaint.date_created}.\n"
            f"Описание: {complaint.description}"
        )
        adr_user = await get_user(complaint.adresat)
        adr_user.reiting -= fine
        await update_user(adr_user)
    else:
        if adr.role == 'Участник':
            await bot.send_message(
                complaint.adresat,
                "На вас пришла новая жалоба от участника.\n"
                f"Время жалобы: {complaint.date_created}.\n"
                f"Категория жалобы: {complaint.violetion}.\n"
                f"Штраф: {fine}.\n"
                f"Описание: {complaint.description}",
                reply_markup=get_agree_disagree_keyboard()
            )
        else:
            await bot.send_message(
                complaint.adresat,
                "На вас пришла новая жалоба от участника.\n"
                f"Время жалобы: {complaint.date_created}.\n"
                f"Категория жалобы: {complaint.violetion}.\n"
                f"Штраф: {fine}.\n"
                f"Описание: {complaint.description}",
            )

async def main():
    global bot_instance
    bot_instance = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start_handler, CommandStart())
    dp.include_router(router)

    await load_datastore()
    actives = await get_active_users()
    for i in actives:
        active_sessions[i] = await get_user(i)
    await dp.start_polling(bot_instance)

if __name__ == "__main__":
    asyncio.run(main())

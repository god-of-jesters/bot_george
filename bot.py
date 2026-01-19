import asyncio
import os
from dotenv import load_dotenv
from collections import defaultdict

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery
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
alarm : dict[int: dict[int, int]] = {}
process_al = {}
al = {}
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
        case "help":
            await callback_query.message.answer("не ну рейтинг пиздатая штука, но ты не думай даже разбираться", reply_markup=get_profile_keyboard())

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
            await callback_query.message.answer("Сообщить/Обратиться.\n(Здесь будет форма сообщения.)")

        case "mailing":
            await callback_query.message.answer("Рассылка.\n(Здесь будет модуль рассылки.)")

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
async def show_main_rating_team(callback_query: Message, state: FSMContext):
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
            await callback_query.message.answer(f"Жалобы. {complaint.description}")

        case "participants":
            await callback_query.message.answer("Участники.\n")

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

"""COMPLAINTS"""

@router.callback_query(lambda c: c.data == "complaint_done", ComplaintProcess.waiting_for_complaint_files)
async def finish_complaint_cb(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.answer()
    await add_complaint(complaintes[user_id])

    if complaintes[user_id].category == "alert":
            await notify_all_reiting_team(callback.message.bot, complaintes[user_id], state)

    if user_id in complaintes:
        del complaintes[user_id]

    await callback.message.answer("Жалоба отправлена. Спасибо.")
    await show_main_menu(callback.bot, user_id, state)

@router.callback_query(lambda c: c.data == 'yes' or c.data == 'no', ComplaintReview.stat)
async def process_complaint_fate(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if callback_query.data == 'yes':
        adr = await get_user(al[user_id])
        adr.reiting -= violetion_vines[al[user_id].violetion]
        await update_user(adr)
        await callback_query.bot.send_message(adr.user_id, 
                               f"""
                               Нас вас пришла новая жалоба. Снято {violetion_vines[al[user_id].violetion]} единиц рейтинга.\n
                               Время жалобы: {al[user_id].date_created}.\n
                               Описание: {al[user_id].description}
                               """)
        del adr

        al[user_id].execution = 'done'
        await update_complaint(al[user_id])
        del al[user_id]

        other = await get_oldest_complaint()
        if other:
            if other.status == 'alert':
                
    else:
        adr = await get_user(al[user_id])
        await callback_query.bot.send_message(adr.user_id, f'На вас была подана жалоба. Команда рейтинга посчитала, что жалоба недействительна')
        del adr

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
        if user == active_sessions[user_id]:
            await message.answer('Нельзя подать жалобу на себя же. Введите еще раз номер бейджа')
            await state.set_state(ComplaintProcess.waiting_for_badge)
            return
        complaintes[user_id].adresat = user.user_id
        
        await message.answer(text="Выберете категорию жалобы.", reply_markup=get_complaint_category_keyboard())
        await state.set_state(ComplaintProcess.waiting_for_complaint_category)
    else:
        await message.answer('Такого человека не существует, введите номер бейджа еще раз')
        return

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
    match complaintes[user_id].category:
        case 'alert':
            complaintes[user_id].violetion = c1[data]
        case 'soon':
            complaintes[user_id].violetion = c2[data]
        case _:
            complaintes[user_id].violetion = c3[data]

    await callback_query.message.answer("Опишите вашу жалобу подробно.")
    await state.set_state(ComplaintProcess.waiting_for_complaint_text)

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
        complaintes[user_id].category = data
        match data:
            case 'alert':
                await callback_query.bot.send_message(user_id, text_alert, reply_markup=get_alert_keyboard())
            case 'soon':
                await callback_query.bot.send_message(user_id, text_soon, reply_markup=get_soon_keyboard())
            case _:
                await callback_query.bot.send_message(user_id, text_other, reply_markup=get_other_keyboard())
        await state.set_state(ComplaintProcess.waiting_for_violation_type)

@router.message(ComplaintProcess.waiting_for_complaint_text)
async def process_complaint_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in complaintes:
        complaintes[user_id].description = message.text
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

    if getattr(complaint, "category", None) == "alert":
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
    await link_files_to_complaint(complaint_id, complaint.files)

    if getattr(complaint, "category", None) == "alert":
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
            await add_file(file)
            complaint.files.append(file.file_id)
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
            await add_file(file)
            complaint.files.append(file.file_id)
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

"""REGISTRATION"""

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
    await add_active(user_id)
    await show_main_menu(message.bot, user_id, state)

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
    for id in team:
        await bot.send_message(id, f"Пришла срочная жалоба! Ответить на нее?", reply_markup=get_yes_no_keyboard())
        if id not in alarm:
            alarm[id] = []
        com = await get_oldest_complaint()
        if com:
            alarm[id].append[com.complaint_id]

async def notify_persone(bot: Bot, complaint: Complaint, state: FSMContext):
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
    if fr.badge_number < 100:
        await bot.send_message(complaint.adresat, 
                               f"""
                               Нас вас пришла новая жалоба от организатора. Снято {violetion_vines[complaint.violetion]} единиц рейтинга.\n
                               Время жалобы: {complaint.date_created}.\n
                               Описание: {complaint.description}
                               """)
        active_sessions[complaint.adresat] -= violetion_vines[complaint.violetion]
        await update_user(active_sessions[complaint.adresat])
    else:
        await bot.send_message(complaint.adresat, f"""
                               Нас вас пришла новая жалоба от участника.\n
                               Время жалобы: {complaint.date_created}.\n
                               Категория жалобы: {complaint.violetion}.\n
                               Штраф: {violetion_vines[complaint.violetion]}.\n
                               Описание: {complaint.description} 
                               """, reply_markup=get_agree_disagree_keyboard())
        special_step[complaint.adresat] = complaint

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
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
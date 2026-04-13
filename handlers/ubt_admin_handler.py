from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import admin_main_kb, ubt_admin_main_kb, ubt_subject_list_kb, ubt_question_type_kb
from config import ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ═══ STATES ═══════════════════════════════════════════════════════════════

class UBTSubjectAdd(StatesGroup):
    name = State()
    confirm = State()


class UBTQuestionAdd(StatesGroup):
    subject = State()
    question_type = State()
    question_text = State()
    context_text = State()

    # Simple/Context/Multiple
    option_a = State()
    option_b = State()
    option_c = State()
    option_d = State()
    correct = State()
    correct_multiple = State()

    # Matching
    matching_left = State()
    matching_right = State()
    matching_answer = State()

    image = State()  # NEW
    confirm = State()


# ═══ ҰБТ ADMIN MAIN ═══════════════════════════════════════════════════════

@router.message(F.text == "📚 ҰБТ басқару")
async def ubt_admin_menu(message: Message):
    if not is_admin(message.from_user.id):
        return

    subjects = await db.get_ubt_subjects()
    mandatory = [s for s in subjects if s['is_mandatory']]
    elective = [s for s in subjects if not s['is_mandatory']]

    text = (
        f"📚 *ҰБТ Басқару*\n\n"
        f"🎓 Міндетті пәндер: {len(mandatory)}\n"
        f"📖 Таңдау пәндері: {len(elective)}\n\n"
        f"_Қажетті бөлімді таңдаңыз:_"
    )

    await message.answer(text, reply_markup=ubt_admin_main_kb())


@router.message(F.text == "🎓 Міндетті пәндер")
async def mandatory_subjects_menu(message: Message):
    if not is_admin(message.from_user.id):
        return

    # Get mandatory subjects
    math_subj = await db.get_ubt_subject_by_name("Математикалық сауаттылық")
    read_subj = await db.get_ubt_subject_by_name("Оқу сауаттылығы")
    hist_subj = await db.get_ubt_subject_by_name("Қазақстан тарихы")

    # Count questions
    math_count = await db.count_ubt_questions(math_subj["id"], "simple") if math_subj else 0
    read_count = await db.count_ubt_questions(read_subj["id"], "simple") if read_subj else 0
    hist_simple = await db.count_ubt_questions(hist_subj["id"], "simple") if hist_subj else 0
    hist_context = await db.count_ubt_questions(hist_subj["id"], "context") if hist_subj else 0

    text = (
        f"🎓 *Міндетті пәндер*\n\n"
        f"📊 *Сұрақтар саны:*\n\n"
        f"🔢 *Математикалық сауаттылық:* {math_count}/10\n"
        f"   • Simple сұрақтар\n\n"
        f"📖 *Оқу сауаттылығы:* {read_count}/10\n"
        f"   • Simple сұрақтар\n\n"
        f"📜 *Қазақстан тарихы:* {hist_simple + hist_context}/20\n"
        f"   • Simple: {hist_simple}/10\n"
        f"   • Context: {hist_context}/10\n\n"
        f"_Пән таңдаңыз:_"
    )

    # Create inline keyboard
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    if math_subj:
        builder.button(text=f"🔢 Мат.сауаттылық ({math_count}/10)", callback_data=f"mand_subj:{math_subj['id']}")
    if read_subj:
        builder.button(text=f"📖 Оқу сауаттылығы ({read_count}/10)", callback_data=f"mand_subj:{read_subj['id']}")
    if hist_subj:
        builder.button(text=f"📜 ҚЗ тарихы ({hist_simple + hist_context}/20)", callback_data=f"mand_subj:{hist_subj['id']}")

    builder.button(text="🔙 Артқа", callback_data="ubt_back_main")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())


# ═══ SUBJECT MANAGEMENT ═══════════════════════════════════════════════════

@router.callback_query(F.data.startswith("mand_subj:"))
async def mandatory_subject_chosen(callback: CallbackQuery, state: FSMContext):
    """Show options for mandatory subject."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ", show_alert=True)
        return

    subject_id = int(callback.data.split(":")[1])
    subject = await db.get_ubt_subject_by_id(subject_id)

    # Count questions by type
    if subject['name'] == "Қазақстан тарихы":
        simple_count = await db.count_ubt_questions(subject_id, "simple")
        context_count = await db.count_ubt_questions(subject_id, "context")
        total = simple_count + context_count

        types_text = (
            f"   • Simple: {simple_count}/10\n"
            f"   • Context: {context_count}/10"
        )
    else:
        total = await db.count_ubt_questions(subject_id, "simple")
        types_text = f"   • Simple: {total}/10"

    text = (
        f"📚 *{subject['name']}*\n\n"
        f"📊 Жалпы: {total}\n"
        f"{types_text}\n\n"
        f"_Не істейсіз?_"
    )

    # Create keyboard
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Сұрақ қосу", callback_data=f"mand_add_q:{subject_id}")
    builder.button(text="📋 Сұрақтарды көру", callback_data=f"mand_list_q:{subject_id}")
    builder.button(text="🔙 Артқа", callback_data="mand_back")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "mand_back")
async def mandatory_back(callback: CallbackQuery):
    """Go back to mandatory subjects list."""
    if not is_admin(callback.from_user.id):
        return

    await callback.message.delete()

    # Resend menu
    message = callback.message
    await mandatory_subjects_menu(message)


@router.callback_query(F.data == "ubt_back_main")
async def ubt_back_main(callback: CallbackQuery):
    """Go back to UBT main menu."""
    if not is_admin(callback.from_user.id):
        return

    await callback.message.delete()


@router.message(F.text == "📋 Таңдау пәндері")
async def ubt_subjects_list(message: Message):
    if not is_admin(message.from_user.id):
        return

    subjects = await db.get_ubt_subjects(is_mandatory=False)

    if not subjects:
        await message.answer(
            "📋 Таңдау пәндері жоқ.\n\n"
            "➕ Жаңа пән қосыңыз.",
            reply_markup=ubt_admin_main_kb()
        )
        return

    lines = ["📋 *Таңдау пәндері:*\n"]
    for s in subjects:
        count = await db.count_ubt_questions(s['id'])
        lines.append(f"• {s['name']}: {count} сұрақ")

    await message.answer("\n".join(lines), reply_markup=ubt_subject_list_kb(subjects))


@router.callback_query(F.data.startswith("ubt_subj:"))
async def elective_subject_chosen(callback: CallbackQuery):
    """Show options for elective subject."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ", show_alert=True)
        return

    subject_id = int(callback.data.split(":")[1])
    subject = await db.get_ubt_subject_by_id(subject_id)

    if not subject:
        await callback.answer("Пән табылмады", show_alert=True)
        return

    # Count questions by type
    simple = await db.count_ubt_questions(subject_id, "simple")
    context = await db.count_ubt_questions(subject_id, "context")
    matching = await db.count_ubt_questions(subject_id, "matching")
    multiple = await db.count_ubt_questions(subject_id, "multiple")
    total = simple + context + matching + multiple

    text = (
        f"📖 *{subject['name']}*\n\n"
        f"📊 *Сұрақтар саны:* {total}/40\n\n"
        f"   • Simple: {simple}/25\n"
        f"   • Context: {context}/5\n"
        f"   • Matching: {matching}/5\n"
        f"   • Multiple: {multiple}/5\n\n"
        f"_Не істейсіз?_"
    )

    # Create keyboard
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Сұрақ қосу", callback_data=f"elec_add_q:{subject_id}")
    builder.button(text="📋 Сұрақтарды көру", callback_data=f"elec_list_q:{subject_id}")
    builder.button(text="🗑 Пәнді өшіру", callback_data=f"elec_del_subj:{subject_id}")
    builder.button(text="🔙 Артқа", callback_data="elec_back")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "elec_back")
async def elective_back(callback: CallbackQuery):
    """Go back to elective subjects list."""
    if not is_admin(callback.from_user.id):
        return

    await callback.message.delete()


@router.callback_query(F.data.startswith("elec_add_q:"))
async def elective_add_question(callback: CallbackQuery, state: FSMContext):
    """Start adding question to elective subject."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ", show_alert=True)
        return

    subject_id = int(callback.data.split(":")[1])
    subject = await db.get_ubt_subject_by_id(subject_id)

    # Show question type selection
    text = (
        f"📖 *{subject['name']} — Сұрақ қосу*\n\n"
        f"Сұрақ түрін таңда:"
    )

    await callback.message.edit_text(text, reply_markup=ubt_question_type_kb())
    await state.update_data(subject_id=subject_id)
    await state.set_state(UBTQuestionAdd.question_type)


@router.callback_query(F.data.startswith("elec_list_q:"))
async def elective_list_questions(callback: CallbackQuery):
    """List questions for elective subject."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ", show_alert=True)
        return

    subject_id = int(callback.data.split(":")[1])
    subject = await db.get_ubt_subject_by_id(subject_id)

    # Get questions
    questions = await db.get_ubt_questions_by_subject(subject_id)

    if not questions:
        await callback.answer("Сұрақтар жоқ", show_alert=True)
        return

    text = f"📋 *{subject['name']} — Сұрақтар ({len(questions)})*\n\n"

    type_emoji = {
        "simple": "📝",
        "context": "💬",
        "matching": "🔗",
        "multiple": "✅"
    }

    for i, q in enumerate(questions[:20], 1):  # First 20
        emoji = type_emoji.get(q['question_type'], "❓")
        text += f"{i}. {emoji} {q['question_text'][:40]}...\n"

    if len(questions) > 20:
        text += f"\n_... және тағы {len(questions) - 20} сұрақ_"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Артқа", callback_data=f"ubt_subj:{subject_id}")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("elec_del_subj:"))
async def elective_delete_subject(callback: CallbackQuery):
    """Delete elective subject."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ", show_alert=True)
        return

    subject_id = int(callback.data.split(":")[1])
    subject = await db.get_ubt_subject_by_id(subject_id)

    # Check if has questions
    count = await db.count_ubt_questions(subject_id)

    if count > 0:
        await callback.answer(
            f"⚠️ Алдымен {count} сұрақты өшіріңіз!",
            show_alert=True
        )
        return

    # Delete subject
    await db.delete_ubt_subject(subject_id)

    await callback.answer(f"✅ {subject['name']} өшірілді!", show_alert=True)
    await callback.message.delete()


@router.message(F.text == "➕ Пән қосу")
async def ubt_add_subject_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(UBTSubjectAdd.name)
    await message.answer(
        "➕ *Жаңа таңдау пәні*\n\n"
        "Пән атауын жазыңыз:\n\n"
        "Мысалы: Информатика, Физика, Биология\n\n"
        "Болдырмау: /cancel"
    )


@router.message(UBTSubjectAdd.name, F.text == "/cancel")
async def ubt_add_subject_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Болдырылмады", reply_markup=ubt_admin_main_kb())


@router.message(UBTSubjectAdd.name)
async def ubt_add_subject_name(message: Message, state: FSMContext):
    name = message.text.strip()

    existing = await db.get_ubt_subject_by_name(name)
    if existing:
        await message.answer(
            f"⚠️ '{name}' пәні бұрыннан бар!\n\n"
            "Басқа атау жазыңыз немесе /cancel"
        )
        return

    await state.update_data(name=name)
    await state.set_state(UBTSubjectAdd.confirm)

    await message.answer(
        f"✅ Пән: *{name}*\n\n"
        f"Сұрақтар саны: 40 (әдепкі)\n\n"
        f"Растау үшін /save, болдырмау /cancel"
    )


@router.message(UBTSubjectAdd.confirm, F.text == "/cancel")
async def ubt_add_subject_confirm_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Болдырылмады", reply_markup=ubt_admin_main_kb())


@router.message(UBTSubjectAdd.confirm, F.text == "/save")
async def ubt_add_subject_save(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']

    subject_id = await db.add_ubt_subject(
        name=name,
        is_mandatory=0,
        questions_count=40,
        time_minutes=90
    )

    await state.clear()

    await message.answer(
        f"✅ *Таңдау пәні қосылды!*\n\n"
        f"Пән: {name}\n"
        f"ID: {subject_id}\n"
        f"Сұрақтар: 40 (әдепкі)\n\n"
        f"Енді бұл пәнге сұрақтар қоса аласыз.",
        reply_markup=ubt_admin_main_kb()
    )


# ═══ MANDATORY SUBJECT QUESTION MANAGEMENT ═══════════════════════════════

@router.callback_query(F.data.startswith("mand_add_q:"))
async def mandatory_add_question_start(callback: CallbackQuery, state: FSMContext):
    """Start adding question to mandatory subject."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ", show_alert=True)
        return

    subject_id = int(callback.data.split(":")[1])
    subject = await db.get_ubt_subject_by_id(subject_id)

    # Determine question type based on subject
    if subject['name'] == "Қазақстан тарихы":
        # Can add Simple or Context
        text = (
            f"📜 *{subject['name']} — Сұрақ қосу*\n\n"
            f"Сұрақ түрін таңда:\n"
            f"• *Simple* — Бір дұрыс жауапты таңдау (10 сұрақ)\n"
            f"• *Context* — Мәнмәтін бойынша (10 сұрақ)\n\n"
            f"_Қай түрді қосасыз?_"
        )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="Simple", callback_data=f"mand_qtype:{subject_id}:simple")
        builder.button(text="Context", callback_data=f"mand_qtype:{subject_id}:context")
        builder.button(text="🔙 Артқа", callback_data=f"mand_subj:{subject_id}")
        builder.adjust(2, 1)

        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    else:
        # Only Simple for Math/Reading
        await state.set_state(UBTQuestionAdd.question_text)
        await state.update_data(subject_id=subject_id, question_type="simple")

        await callback.message.edit_text(
            f"📝 *{subject['name']} — Simple сұрақ*\n\n"
            f"Сұрақты жазыңыз:"
        )


@router.callback_query(F.data.startswith("mand_qtype:"))
async def mandatory_question_type_chosen(callback: CallbackQuery, state: FSMContext):
    """Question type chosen for mandatory subject."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ", show_alert=True)
        return

    parts = callback.data.split(":")
    subject_id = int(parts[1])
    qtype = parts[2]

    subject = await db.get_ubt_subject_by_id(subject_id)

    await state.set_state(UBTQuestionAdd.question_text)
    await state.update_data(subject_id=subject_id, question_type=qtype)

    await callback.message.edit_text(
        f"📝 *{subject['name']} — {qtype.capitalize()} сұрақ*\n\n"
        f"Сұрақты жазыңыз:"
    )


@router.callback_query(F.data.startswith("mand_list_q:"))
async def mandatory_list_questions(callback: CallbackQuery):
    """List questions for mandatory subject."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ", show_alert=True)
        return

    subject_id = int(callback.data.split(":")[1])
    subject = await db.get_ubt_subject_by_id(subject_id)

    # Get questions
    questions = await db.get_ubt_questions_by_subject(subject_id)

    if not questions:
        await callback.answer("Сұрақтар жоқ", show_alert=True)
        return

    text = f"📋 *{subject['name']} — Сұрақтар ({len(questions)})*\n\n"

    for i, q in enumerate(questions[:20], 1):  # First 20
        qtype_emoji = "📝" if q['question_type'] == "simple" else "💬"
        text += f"{i}. {qtype_emoji} {q['question_text'][:40]}...\n"

    if len(questions) > 20:
        text += f"\n_... және тағы {len(questions) - 20} сұрақ_"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Артқа", callback_data=f"mand_subj:{subject_id}")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


# ═══ QUESTION ADD (ELECTIVE) ══════════════════════════════════════════════

@router.message(F.text == "➕ ҰБТ сұрағы қосу")
async def ubt_add_question_redirect(message: Message):
    """Redirect to proper menus."""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "ℹ️ *Сұрақ қосу үшін:*\n\n"
        "🎓 *Міндетті пәндер* — Міндетті пән таңда → ➕ Сұрақ қосу\n\n"
        "📋 *Таңдау пәндері* — Пән таңда → ➕ Сұрақ қосу\n\n"
        "_Қажетті бөлімге өтіңіз:_",
        reply_markup=ubt_admin_main_kb()
    )


@router.message(UBTQuestionAdd.subject, F.text == "/cancel")
async def ubt_add_q_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Болдырылмады", reply_markup=ubt_admin_main_kb())


@router.message(UBTQuestionAdd.subject)
async def ubt_add_q_subject(message: Message, state: FSMContext):
    try:
        subject_id = int(message.text.strip())
        subject = await db.get_ubt_subject_by_id(subject_id)

        if not subject:
            await message.answer("⚠️ Пән табылмады! ID қайтадан жазыңыз:")
            return

        await state.update_data(subject_id=subject_id, subject_name=subject['name'])
        await state.set_state(UBTQuestionAdd.question_type)

        await message.answer(
            f"📚 Пән: *{subject['name']}*\n\n"
            f"Сұрақ түрін таңдаңыз:",
            reply_markup=ubt_question_type_kb()
        )
    except ValueError:
        await message.answer("⚠️ Дұрыс емес! Сан жазыңыз (мысалы: 1)")


@router.callback_query(UBTQuestionAdd.question_type, F.data.startswith("ubtq_type:"))
async def ubt_add_q_type(callback: CallbackQuery, state: FSMContext):
    qtype = callback.data.split(":")[1]

    await state.update_data(question_type=qtype)
    await state.set_state(UBTQuestionAdd.question_text)

    type_names = {
        "simple": "Бір дұрыс жауап",
        "context": "Контекст бойынша",
        "matching": "Сәйкестік",
        "multiple": "Бірнеше дұрыс жауап"
    }

    await callback.message.edit_text(
        f"📝 Түрі: *{type_names[qtype]}*\n\n"
        f"Сұрақ мәтінін жазыңыз:"
    )


@router.message(UBTQuestionAdd.question_text)
async def ubt_add_q_text(message: Message, state: FSMContext):
    await state.update_data(question_text=message.text)
    data = await state.get_data()
    qtype = data['question_type']

    if qtype == 'context':
        await state.set_state(UBTQuestionAdd.context_text)
        await message.answer(
            "💬 *Контекст/Мәнмәтін жазыңыз:*\n\n"
            "Мысалы: \"Қазақстан 1991 жылы тәуелсіздік алды...\"\n\n"
            "Немесе өткізіп жіберу: /skip"
        )
    elif qtype == 'matching':
        await state.set_state(UBTQuestionAdd.matching_left)
        await message.answer(
            "🔢 *Сол жақ тізімді жазыңыз* (әр жолға бір элемент):\n\n"
            "Мысалы:\n"
            "Астана\n"
            "Алматы\n"
            "Шымкент"
        )
    else:
        await state.set_state(UBTQuestionAdd.option_a)
        await message.answer("A) нұсқасын жазыңыз:")


# Context flow
@router.message(UBTQuestionAdd.context_text, F.text == "/skip")
async def ubt_add_q_skip_context(message: Message, state: FSMContext):
    await state.update_data(context_text=None)
    await state.set_state(UBTQuestionAdd.option_a)
    await message.answer("A) нұсқасын жазыңыз:")


@router.message(UBTQuestionAdd.context_text)
async def ubt_add_q_context(message: Message, state: FSMContext):
    await state.update_data(context_text=message.text)
    await state.set_state(UBTQuestionAdd.option_a)
    await message.answer("A) нұсқасын жазыңыз:")


# Options A,B,C,D
@router.message(UBTQuestionAdd.option_a)
async def ubt_add_q_opt_a(message: Message, state: FSMContext):
    await state.update_data(option_a=message.text)
    await state.set_state(UBTQuestionAdd.option_b)
    await message.answer("B) нұсқасын жазыңыз:")


@router.message(UBTQuestionAdd.option_b)
async def ubt_add_q_opt_b(message: Message, state: FSMContext):
    await state.update_data(option_b=message.text)
    await state.set_state(UBTQuestionAdd.option_c)
    await message.answer("C) нұсқасын жазыңыз:")


@router.message(UBTQuestionAdd.option_c)
async def ubt_add_q_opt_c(message: Message, state: FSMContext):
    await state.update_data(option_c=message.text)
    await state.set_state(UBTQuestionAdd.option_d)
    await message.answer("D) нұсқасын жазыңыз:")


@router.message(UBTQuestionAdd.option_d)
async def ubt_add_q_opt_d(message: Message, state: FSMContext):
    await state.update_data(option_d=message.text)
    data = await state.get_data()

    if data['question_type'] == 'multiple':
        await state.set_state(UBTQuestionAdd.correct_multiple)
        await message.answer(
            "✅ *Дұрыс жауаптарды таңдаңыз* (бірнеше болуы мүмкін):\n\n"
            "Мысалы: A,C,D немесе B,D\n\n"
            "Үтір арқылы бөліңіз!"
        )
    else:
        await state.set_state(UBTQuestionAdd.correct)
        await message.answer("✅ Дұрыс жауапты таңдаңыз (A, B, C немесе D):")


@router.message(UBTQuestionAdd.correct)
async def ubt_add_q_correct(message: Message, state: FSMContext):
    correct = message.text.strip().upper()

    if correct not in ['A', 'B', 'C', 'D']:
        await message.answer("⚠️ A, B, C немесе D жазыңыз!")
        return

    await state.update_data(correct=correct)
    await state.set_state(UBTQuestionAdd.image)
    await message.answer(
        "🖼 *Сурет қосу (міндетті емес)*\n\n"
        "Сурет жүктеңіз немесе URL жазыңыз\n\n"
        "/skip — өткізіп жіберу"
    )


@router.message(UBTQuestionAdd.correct_multiple)
async def ubt_add_q_correct_mult(message: Message, state: FSMContext):
    correct = message.text.strip().upper().replace(" ", "")

    parts = correct.split(",")
    for p in parts:
        if p not in ['A', 'B', 'C', 'D']:
            await message.answer("⚠️ A,B,C,D форматында жазыңыз! (Мысалы: A,C,D)")
            return

    await state.update_data(correct_multiple=correct)
    await state.set_state(UBTQuestionAdd.image)
    await message.answer(
        "🖼 *Сурет қосу (міндетті емес)*\n\n"
        "Сурет жүктеңіз немесе URL жазыңыз\n\n"
        "/skip — өткізіп жіберу"
    )


# Matching flow
@router.message(UBTQuestionAdd.matching_left)
async def ubt_add_q_match_left(message: Message, state: FSMContext):
    items = [line.strip() for line in message.text.split("\n") if line.strip()]

    if len(items) < 2:
        await message.answer("⚠️ Кемінде 2 элемент керек! Қайтадан жазыңыз:")
        return

    await state.update_data(matching_left=items)
    await state.set_state(UBTQuestionAdd.matching_right)

    await message.answer(
        f"✅ Сол жақ: {len(items)} элемент\n\n"
        f"🔢 *Оң жақ тізімді жазыңыз* (бірдей саны):\n\n"
        f"Мысалы:\n"
        f"Астана қаласы\n"
        f"Оңтүстік қала\n"
        f"Ірі қала"
    )


@router.message(UBTQuestionAdd.matching_right)
async def ubt_add_q_match_right(message: Message, state: FSMContext):
    items = [line.strip() for line in message.text.split("\n") if line.strip()]
    data = await state.get_data()
    left = data['matching_left']

    if len(items) != len(left):
        await message.answer(
            f"⚠️ Сол жақта {len(left)} элемент бар, "
            f"оң жақта да {len(left)} болуы керек!\n\n"
            f"Қайтадан жазыңыз:"
        )
        return

    await state.update_data(matching_right=items)
    await state.set_state(UBTQuestionAdd.matching_answer)

    text = "🔗 *Сәйкестікті көрсетіңіз:*\n\n"
    for i, item in enumerate(left):
        text += f"{chr(65+i)}. {item}\n"
    text += "\n"
    for i, item in enumerate(items):
        text += f"{i+1}. {item}\n"
    text += "\nМысалы: A=1,B=3,C=2"

    await message.answer(text)


@router.message(UBTQuestionAdd.matching_answer)
async def ubt_add_q_match_answer(message: Message, state: FSMContext):
    answer_text = message.text.strip().upper().replace(" ", "")

    try:
        pairs = answer_text.split(",")
        answer_dict = {}
        for pair in pairs:
            letter, number = pair.split("=")
            answer_dict[letter] = number

        await state.update_data(matching_answer=answer_dict)
        await state.set_state(UBTQuestionAdd.image)
        await message.answer(
            "🖼 *Сурет қосу (міндетті емес)*\n\n"
            "Сурет жүктеңіз немесе URL жазыңыз\n\n"
            "/skip — өткізіп жіберу"
        )
    except:
        await message.answer("⚠️ Дұрыс емес формат! Мысалы: A=1,B=3,C=2")


# Image handlers
@router.message(UBTQuestionAdd.image, F.text == "/skip")
async def ubt_skip_image(message: Message, state: FSMContext):
    await state.update_data(image_url=None)
    await show_ubt_preview(message, state)


@router.message(UBTQuestionAdd.image, F.photo)
async def ubt_add_image_photo(message: Message, state: FSMContext):
    """Handle photo upload."""
    photo = message.photo[-1]
    file_id = photo.file_id

    file = await message.bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"

    await state.update_data(image_url=file_url, image_file_id=file_id)
    await message.answer("✅ Сурет сақталды!")
    await show_ubt_preview(message, state)


@router.message(UBTQuestionAdd.image)
async def ubt_add_image_url(message: Message, state: FSMContext):
    """Handle URL."""
    url = message.text.strip()

    if url.startswith(("http://", "https://")):
        await state.update_data(image_url=url)
        await message.answer("✅ Сурет URL сақталды.")
        await show_ubt_preview(message, state)
    else:
        await message.answer(
            "⚠️ Дұрыс URL (http://...) немесе суретті жүктеңіз\n"
            "/skip — өткізіп жіберу"
        )


# Preview and Save
async def show_ubt_preview(message: Message, state: FSMContext):
    """Show preview before saving."""
    data = await state.get_data()
    qtype = data['question_type']

    preview = (
        f"📋 *Алдын ала қарау:*\n\n"
        f"📚 Пән: {data['subject_name']}\n"
        f"📝 Түрі: {qtype}\n"
        f"❓ Сұрақ: {data['question_text']}\n\n"
    )

    if qtype == 'context' and data.get('context_text'):
        preview += f"💬 Контекст: {data['context_text'][:50]}...\n\n"

    if qtype in ['simple', 'context', 'multiple']:
        preview += (
            f"A) {data['option_a']}\n"
            f"B) {data['option_b']}\n"
            f"C) {data['option_c']}\n"
            f"D) {data['option_d']}\n\n"
        )
        if qtype == 'multiple':
            preview += f"✅ Дұрыс: {data['correct_multiple']}\n\n"
        else:
            preview += f"✅ Дұрыс: {data['correct']}\n\n"

    elif qtype == 'matching':
        preview += "🔗 Сәйкестік:\n"
        for i, item in enumerate(data['matching_left']):
            preview += f"{chr(65+i)}. {item}\n"
        preview += "\n"
        for i, item in enumerate(data['matching_right']):
            preview += f"{i+1}. {item}\n"
        preview += f"\n✅ Жауап: {data['matching_answer']}\n\n"

    # Add image if present
    if data.get('image_url'):
        preview += f"🖼 Сурет: {data['image_url'][:50]}...\n\n"

    preview += "Сақтау: /save, Болдырмау: /cancel"

    await state.set_state(UBTQuestionAdd.confirm)
    await message.answer(preview)


@router.message(UBTQuestionAdd.confirm, F.text == "/cancel")
async def ubt_add_q_confirm_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Болдырылмады", reply_markup=ubt_admin_main_kb())


@router.message(UBTQuestionAdd.confirm, F.text == "/save")
async def ubt_add_q_save(message: Message, state: FSMContext):
    data = await state.get_data()

    question_id = await db.add_ubt_question(
        subject_id=data['subject_id'],
        question_type=data['question_type'],
        question_text=data['question_text'],
        **data
    )

    await state.clear()

    await message.answer(
        f"✅ *ҰБТ сұрағы қосылды!*\n\n"
        f"ID: {question_id}\n"
        f"Түрі: {data['question_type']}\n"
        f"Пән: {data['subject_name']}",
        reply_markup=ubt_admin_main_kb()
    )


# ═══ STATISTICS ═══════════════════════════════════════════════════════════

@router.message(F.text == "📊 ҰБТ статистика")
async def ubt_admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    subjects = await db.get_ubt_subjects()

    lines = ["📊 *ҰБТ Статистика:*\n"]

    for s in subjects:
        emoji = "🎓" if s['is_mandatory'] else "📖"
        total = await db.count_ubt_questions(s['id'])

        simple = await db.count_ubt_questions(s['id'], 'simple')
        context = await db.count_ubt_questions(s['id'], 'context')
        matching = await db.count_ubt_questions(s['id'], 'matching')
        multiple = await db.count_ubt_questions(s['id'], 'multiple')

        # Міндетті пәндерге тек керектілерін көрсет
        if s['is_mandatory']:
            if s['name'] == "Қазақстан тарихы":
                lines.append(
                    f"{emoji} *{s['name']}*: {total}/20\n"
                    f"   • Simple: {simple}/10\n"
                    f"   • Context: {context}/10\n"
                )
            else:
                lines.append(
                    f"{emoji} *{s['name']}*: {total}/10\n"
                    f"   • Simple: {simple}/10\n"
                )
        else:
            # Таңдау пәндерге барлығын көрсет
            lines.append(
                f"{emoji} *{s['name']}*: {total}/40\n"
                f"   • Simple: {simple}/25\n"
                f"   • Context: {context}/5\n"
                f"   • Matching: {matching}/5\n"
                f"   • Multiple: {multiple}/5\n"
            )

    await message.answer("\n".join(lines), reply_markup=ubt_admin_main_kb())


@router.message(F.text == "⚙️ ҰБТ баптаулар")
async def ubt_settings(message: Message):
    if not is_admin(message.from_user.id):
        return

    settings = await db.get_bot_settings()

    text = (
        "⚙️ *ҰБТ Баптаулары*\n\n"
        "_Әзірге әдепкі Quiz баптаулары қолданылады._\n\n"
        "Келесі версияда:\n"
        "• ҰБТ уақытын өзгерту\n"
        "• Shuffle on/off\n"
        "• Шекті баллдар\n\n"
        "_Жұмыс жүріп жатыр... 🚧_"
    )

    await message.answer(text, reply_markup=ubt_admin_main_kb())


@router.message(F.text == "🔙 Әкімші тақтасы")
async def ubt_back_to_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer("👨‍💼 Әкімші тақтасы", reply_markup=admin_main_kb())
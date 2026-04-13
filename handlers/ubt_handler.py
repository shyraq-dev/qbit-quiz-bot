from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import random
import json

import database as db
from keyboards import main_menu_kb, ubt_mode_kb, ubt_subjects_kb

router = Router()


class UBTState(StatesGroup):
    choosing_mode = State()
    choosing_elective1 = State()
    choosing_elective2 = State()
    in_ubt = State()


# ═══ ҰБТ CONSTANTS ═══

# Міндетті пәндер (ДҰРЫС сандар!)
MANDATORY_SUBJECTS = {
    "Математикалық сауаттылық": {"count": 10, "points": 10},
    "Оқу сауаттылығы": {"count": 10, "points": 10},
    "Қазақстан тарихы": {"count": 20, "points": 20}
}

# Таңдау пәндері
ELECTIVE_CONFIG = {
    "simple": 25,      # Бір дұрыс жауап
    "context": 5,      # Контекст
    "matching": 5,     # Сәйкестік
    "multiple": 5,     # Бірнеше дұрыс
    "total": 40,       # Жалпы
    "points": 50       # Балл
}

# ЖАЛПЫ: 120 сұрақ, 140 балл


# ═══ MAIN MENU ═══

@router.message(F.text == "📚 ҰБТ режимі")
async def ubt_menu(message: Message, state: FSMContext):
    await state.clear()

    text = (
        "📚 *ҰБТ режимі*\n\n"
        "🎓 *Міндетті пәндер:*\n"
        "  • Оқу сауаттылығы (10 сұрақ, 10 балл)\n"
        "  • Математикалық сауаттылық (10 сұрақ, 10 балл)\n"
        "  • Қазақстан тарихы (20 сұрақ, 20 балл)\n\n"
        "📖 *Таңдау пәндері:* 2 пән таңда (әрқайсысы 40 сұрақ, 50 балл)\n\n"
        "⏱ *Уақыт:*\n"
        "  • Толық тест: 180 минут (3 сағат)\n"
        "  • Қысқартылған: 60 минут\n\n"
        "🎯 *Максимум балл:* 140\n\n"
        "_Қандай режимді таңдайсың?_"
    )

    await state.set_state(UBTState.choosing_mode)
    await message.answer(text, reply_markup=ubt_mode_kb())


@router.callback_query(UBTState.choosing_mode, F.data.startswith("ubt_mode:"))
async def ubt_mode_chosen(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]

    await state.update_data(mode=mode)

    # Get available elective subjects
    subjects = await db.get_ubt_subjects(is_mandatory=False)

    if len(subjects) < 2:
        await callback.answer(
            "⚠️ Таңдау пәндері әлі қосылмаған. Админмен хабарласыңыз.",
            show_alert=True
        )
        return

    await state.set_state(UBTState.choosing_elective1)

    time_text = "180 минут (3 сағат)" if mode == "full" else "60 минут"

    await callback.message.edit_text(
        f"📖 *Бірінші таңдау пәнін таңда:*\n\n"
        f"⏱ Режим: {time_text}\n\n"
        f"_Екі пән таңдауың керек_",
        reply_markup=ubt_subjects_kb(subjects, exclude=[])
    )


@router.callback_query(UBTState.choosing_elective1, F.data.startswith("ubt_elective:"))
async def elective1_chosen(callback: CallbackQuery, state: FSMContext):
    subject_id = int(callback.data.split(":")[1])

    await state.update_data(elective1_id=subject_id)

    subjects = await db.get_ubt_subjects(is_mandatory=False)

    await state.set_state(UBTState.choosing_elective2)

    await callback.message.edit_text(
        "📖 *Екінші таңдау пәнін таңда:*",
        reply_markup=ubt_subjects_kb(subjects, exclude=[subject_id])
    )


@router.callback_query(UBTState.choosing_elective2, F.data.startswith("ubt_elective:"))
async def elective2_chosen(callback: CallbackQuery, state: FSMContext):
    subject_id = int(callback.data.split(":")[1])
    data = await state.get_data()

    if subject_id == data.get("elective1_id"):
        await callback.answer("⚠️ Бірдей пәнді екі рет таңдай алмайсың!", show_alert=True)
        return

    await state.update_data(elective2_id=subject_id)

    await start_ubt_test(callback, state)


# ═══ START TEST ═══

async def start_ubt_test(callback: CallbackQuery, state: FSMContext):
    """Initialize and start UBT test."""
    data = await state.get_data()
    user_id = callback.from_user.id

    mode = data["mode"]
    elective1_id = data["elective1_id"]
    elective2_id = data["elective2_id"]

    # Get elective names
    e1 = await db.get_ubt_subject_by_id(elective1_id)
    e2 = await db.get_ubt_subject_by_id(elective2_id)

    # Collect questions from all subjects
    all_questions = []

    # 1. Міндетті пәндер (тек simple!)
    # Математикалық сауаттылық: 10 simple
    math_subj = await db.get_ubt_subject_by_name("Математикалық сауаттылық")
    if math_subj:
        math_q = await db.get_ubt_questions_by_subject(
            math_subj["id"],
            question_type="simple",
            limit=10
        )
        for q in math_q:
            q["subject_name"] = "Математикалық сауаттылық"
            q["subject_type"] = "mandatory"
            q["points_value"] = 1
        all_questions.extend(math_q)

    # Оқу сауаттылығы: 10 simple
    read_subj = await db.get_ubt_subject_by_name("Оқу сауаттылығы")
    if read_subj:
        read_q = await db.get_ubt_questions_by_subject(
            read_subj["id"],
            question_type="simple",
            limit=10
        )
        for q in read_q:
            q["subject_name"] = "Оқу сауаттылығы"
            q["subject_type"] = "mandatory"
            q["points_value"] = 1
        all_questions.extend(read_q)

    # Қазақстан тарихы: 10 simple + 10 context
    hist_subj = await db.get_ubt_subject_by_name("Қазақстан тарихы")
    if hist_subj:
        hist_simple = await db.get_ubt_questions_by_subject(
            hist_subj["id"],
            question_type="simple",
            limit=10
        )
        hist_context = await db.get_ubt_questions_by_subject(
            hist_subj["id"],
            question_type="context",
            limit=10
        )
        for q in hist_simple + hist_context:
            q["subject_name"] = "Қазақстан тарихы"
            q["subject_type"] = "mandatory"
            q["points_value"] = 1
        all_questions.extend(hist_simple)
        all_questions.extend(hist_context)

    # 2. Таңдау пән 1 (4 түрі!)
    questions_e1 = await collect_elective_questions(elective1_id, e1["name"], "elective1")
    all_questions.extend(questions_e1)

    # 3. Таңдау пән 2 (4 түрі!)
    questions_e2 = await collect_elective_questions(elective2_id, e2["name"], "elective2")
    all_questions.extend(questions_e2)

    # Check if enough questions
    expected = 40 + 40 + 40  # 10+10+20 + 40 + 40
    if len(all_questions) < expected:
        await callback.message.edit_text(
            f"⚠️ *Жеткіліксіз сұрақтар*\n\n"
            f"Керек: {expected}\n"
            f"Бар: {len(all_questions)}\n\n"
            f"Детальды:\n"
            f"Мат.сауат: {len([q for q in all_questions if q['subject_name']=='Математикалық сауаттылық'])}/10\n"
            f"Оқу сауат: {len([q for q in all_questions if q['subject_name']=='Оқу сауаттылығы'])}/10\n"
            f"ҚЗ тарихы: {len([q for q in all_questions if q['subject_name']=='Қазақстан тарихы'])}/20\n"
            f"{e1['name']}: {len([q for q in all_questions if q['subject_type']=='elective1'])}/40\n"
            f"{e2['name']}: {len([q for q in all_questions if q['subject_type']=='elective2'])}/40\n\n"
            f"Админге хабарласыңыз."
        )
        await state.clear()
        return

    # Shuffle
    settings = await db.get_effective_quiz_settings(user_id)
    if settings.get("shuffle_questions", 1):
        random.shuffle(all_questions)

    # Calculate time
    time_minutes = 180 if mode == "full" else 60

    await state.set_state(UBTState.in_ubt)
    await state.update_data(
        questions=all_questions,
        current=0,
        mandatory_correct=0,
        mandatory_wrong=0,
        elective1_correct=0,
        elective1_wrong=0,
        elective2_correct=0,
        elective2_wrong=0,
        total_correct=0,
        total_wrong=0,
        shuffle_answers=settings.get("shuffle_answers", 1),
        time_limit=time_minutes * 60,
        elective1_name=e1["name"],
        elective2_name=e2["name"],
    )

    await callback.message.delete()

    await callback.message.answer(
        f"🎓 *ҰБТ басталды!*\n\n"
        f"📚 Міндетті: 40 сұрақ (10+10+20)\n"
        f"📖 Таңдау: {e1['name']}, {e2['name']}\n"
        f"⏱ Уақыт: {time_minutes} минут\n\n"
        f"_Бірінші сұраққа өтеміз..._"
    )

    import asyncio
    await asyncio.sleep(1)

    await send_ubt_question(callback.message, state, new_message=True)


async def collect_elective_questions(subject_id: int, subject_name: str,
                                    subject_type: str) -> list[dict]:
    """Collect questions for elective subject."""
    questions = []

    # Get questions by type
    simple = await db.get_ubt_questions_by_subject(
        subject_id,
        question_type="simple",
        limit=ELECTIVE_CONFIG["simple"]
    )
    context = await db.get_ubt_questions_by_subject(
        subject_id,
        question_type="context",
        limit=ELECTIVE_CONFIG["context"]
    )
    matching = await db.get_ubt_questions_by_subject(
        subject_id,
        question_type="matching",
        limit=ELECTIVE_CONFIG["matching"]
    )
    multiple = await db.get_ubt_questions_by_subject(
        subject_id,
        question_type="multiple",
        limit=ELECTIVE_CONFIG["multiple"]
    )

    # Add metadata
    for q in simple + context + matching + multiple:
        q["subject_name"] = subject_name
        q["subject_type"] = subject_type
        q["points_value"] = 1.25  # 50 балл / 40 сұрақ = 1.25

    questions.extend(simple)
    questions.extend(context)
    questions.extend(matching)
    questions.extend(multiple)

    return questions


# ═══ SEND QUESTION ═══

async def send_ubt_question(message: Message, state: FSMContext, new_message: bool = False):
    """Send UBT question (handles 4 types)."""
    data = await state.get_data()
    questions = data["questions"]
    idx = data["current"]

    if idx >= len(questions):
        await finish_ubt(message, state)
        return

    q = questions[idx]
    qtype = q["question_type"]

    # Build question text
    subject_emoji = "🎓" if q["subject_type"] == "mandatory" else "📖"

    header = (
        f"📌 *Сұрақ {idx + 1}/{len(questions)}*\n"
        f"{subject_emoji} _{q['subject_name']}_\n\n"
    )

    # Context if exists
    if q.get('context_text'):
        header += f"💬 {q['context_text']}\n\n"

    # Question
    header += f"*{q['question_text']}*\n\n"

    # Handle different question types
    if qtype in ['simple', 'context', 'multiple']:
        await send_options_question(message, state, q, header, idx)
    elif qtype == 'matching':
        await send_matching_question(message, state, q, header, idx)


async def send_options_question(message: Message, state: FSMContext,
                                q: dict, header: str, idx: int):
    """Send simple/context/multiple question."""
    data = await state.get_data()
    shuffle_answers = data.get("shuffle_answers", 1)

    if shuffle_answers:
        # Shuffle options
        options = {
            "A": q["option_a"],
            "B": q["option_b"],
            "C": q["option_c"],
            "D": q["option_d"],
        }

        if q["question_type"] == "multiple":
            correct_letters = q["correct_multiple"].split(",")
        else:
            correct_letters = [q["correct"]]

        letters = list(options.keys())
        random.shuffle(letters)

        shuffled_options = {}
        new_correct = []
        for new_letter, old_letter in zip(["A", "B", "C", "D"], letters):
            shuffled_options[new_letter] = options[old_letter]
            if old_letter in correct_letters:
                new_correct.append(new_letter)

        await state.update_data(**{
            f"shuffle_map_{idx}": letters,
            f"correct_{idx}": ",".join(sorted(new_correct))
        })

        options_text = (
            f"A) {shuffled_options['A']}\n"
            f"B) {shuffled_options['B']}\n"
            f"C) {shuffled_options['C']}\n"
            f"D) {shuffled_options['D']}\n\n"
        )
    else:
        options_text = (
            f"A) {q['option_a']}\n"
            f"B) {q['option_b']}\n"
            f"C) {q['option_c']}\n"
            f"D) {q['option_d']}\n\n"
        )

        if q["question_type"] == "multiple":
            await state.update_data(**{f"correct_{idx}": q["correct_multiple"]})
        else:
            await state.update_data(**{f"correct_{idx}": q["correct"]})

    # Special instruction for multiple
    if q["question_type"] == "multiple":
        instruction = "👇 *Дұрыс жауаптарды таңда* (бірнеше болуы мүмкін):"
    else:
        instruction = "👇 Жауабыңды таңда:"

    text = header + options_text + instruction

    # Create inline keyboard
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="A", callback_data=f"ubt_ans:{idx}:A")
    builder.button(text="B", callback_data=f"ubt_ans:{idx}:B")
    builder.button(text="C", callback_data=f"ubt_ans:{idx}:C")
    builder.button(text="D", callback_data=f"ubt_ans:{idx}:D")

    if q["question_type"] == "multiple":
        builder.button(text="✅ Растау", callback_data=f"ubt_ans:{idx}:CONFIRM")
        builder.adjust(4, 1)
    else:
        builder.adjust(4)

    await message.answer(text, reply_markup=builder.as_markup())


async def send_matching_question(message: Message, state: FSMContext,
                                q: dict, header: str, idx: int):
    """Send matching question."""
    # Parse JSON
    left = json.loads(q["matching_left"])
    right = json.loads(q["matching_right"])
    answer = json.loads(q["matching_answer"])

    # Build text
    text = header + "🔗 *Сәйкестікті табыңыз:*\n\n"

    for i, item in enumerate(left):
        text += f"{chr(65+i)}. {item}\n"
    text += "\n"
    for i, item in enumerate(right):
        text += f"{i+1}. {item}\n"

    text += "\n_Жауабын жазыңыз (мысалы: A=1,B=2,C=3)_"

    # Store correct answer
    await state.update_data(**{f"correct_{idx}": answer})

    await message.answer(text)


# ═══ ANSWER PROCESSING ═══

@router.callback_query(UBTState.in_ubt, F.data.startswith("ubt_ans:"))
async def process_ubt_answer(callback: CallbackQuery, state: FSMContext):
    """Process UBT answer (simple/context)."""
    parts = callback.data.split(":")
    idx = int(parts[1])
    answer = parts[2]

    data = await state.get_data()

    if answer == "CONFIRM":
        # Multiple choice confirmation
        selected = data.get(f"selected_{idx}", [])
        user_answer = ",".join(sorted(selected))
    else:
        user_answer = answer

    # Get correct answer
    correct_answer = data.get(f"correct_{idx}")
    questions = data["questions"]
    q = questions[idx]

    # Check if correct
    is_correct = (user_answer == correct_answer)

    # Update stats
    await update_ubt_stats(state, q, is_correct)

    # Move to next
    await state.update_data(current=idx + 1)

    # Feedback
    if is_correct:
        await callback.answer("✅ Дұрыс!", show_alert=False)
    else:
        await callback.answer(f"❌ Қате! Дұрысы: {correct_answer}", show_alert=True)

    await callback.message.delete()
    await send_ubt_question(callback.message, state, new_message=True)


@router.message(UBTState.in_ubt)
async def process_ubt_text_answer(message: Message, state: FSMContext):
    """Process matching answer (text input)."""
    data = await state.get_data()
    idx = data["current"]

    user_answer = message.text.strip().upper().replace(" ", "")

    # Parse user answer
    try:
        pairs = user_answer.split(",")
        user_dict = {}
        for pair in pairs:
            letter, number = pair.split("=")
            user_dict[letter] = number
    except:
        await message.answer(
            "⚠️ Дұрыс емес формат!\n\n"
            "Мысалы: A=1,B=2,C=3"
        )                                              return

    # Get correct answer
    correct_dict = data.get(f"correct_{idx}")

    # Check
    is_correct = (user_dict == correct_dict)

    # Update stats
    questions = data["questions"]
    q = questions[idx]
    await update_ubt_stats(state, q, is_correct)

    # Move to next
    await state.update_data(current=idx + 1)

    # Feedback
    if is_correct:
        await message.answer("✅ Дұрыс!")
    else:                                              await message.answer(f"❌ Қате! Дұрысы: {correct_dict}")
                                                   await send_ubt_question(message, state, new_message=True)


async def update_ubt_stats(state: FSMContext, q: dict, is_correct: bool):
    """Update statistics based on subject type."""
    data = await state.get_data()              
    if is_correct:
        data["total_correct"] += 1
                                                       if q["subject_type"] == "mandatory":
            data["mandatory_correct"] += 1
        elif q["subject_type"] == "elective1":
            data["elective1_correct"] += 1
        elif q["subject_type"] == "elective2":
            data["elective2_correct"] += 1         else:
        data["total_wrong"] += 1

        if q["subject_type"] == "mandatory":
            data["mandatory_wrong"] += 1
        elif q["subject_type"] == "elective1":
            data["elective1_wrong"] += 1
        elif q["subject_type"] == "elective2":
            data["elective2_wrong"] += 1

    await state.update_data(**data)


# ═══ FINISH ═══

async def finish_ubt(message: Message, state: FSMContext):
    """Finish UBT and show results."""
    data = await state.get_data()
    user_id = message.chat.id

    # Calculate scores
    mandatory_score = data["mandatory_correct"]  # 1:1 балл
    elective1_score = round(data["elective1_correct"] * 1.25)  # 40 сұрақ → 50 балл
    elective2_score = round(data["elective2_correct"] * 1.25)

    mandatory_total = 40
    elective_total = 100
    total_score = mandatory_score + elective1_score + elective2_score

    total_questions = len(data["questions"])
    accuracy = round(data["total_correct"] / total_questions * 100) if total_questions else 0

    # Grade
    if total_score >= 100:
        badge = "🏆 Өте жақсы"
    elif total_score >= 70:
        badge = "⭐ Жақсы"
    elif total_score >= 50:
        badge = "📚 Қанағаттанарлық"
    else:
        badge = "💪 Жалғастыр"

    e1_name = data.get("elective1_name", "Таңдау 1")
    e2_name = data.get("elective2_name", "Таңдау 2")

    text = (
        f"🎉 *ҰБТ аяқталды!*\n\n"                      f"📊 *Нәтиже: {badge}*\n\n"
        f"🎯 *ЖАЛПЫ БАЛЛ: {total_score}/140*\n\n"
        f"📚 *Міндетті пәндер:* {mandatory_score}/{mandatory_total}\n"
        f"   ✅ Дұрыс: {data['mandatory_correct']}/40\n"
        f"   ❌ Қате: {data['mandatory_wrong']}\n\n"
        f"📖 *{e1_name}:* {elective1_score}/50\n"                                                     f"   ✅ Дұрыс: {data['elective1_correct']}/40\n\n"
        f"📖 *{e2_name}:* {elective2_score}/50\n"
        f"   ✅ Дұрыс: {data['elective2_correct']}/40\n\n"
        f"🎯 Жалпы дәлдік: *{accuracy}%*\n\n"          f"_Керемет! 🎊_"
    )                                          
    await message.answer(text, reply_markup=main_menu_kb())
    await state.clear()
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import aiosqlite
import database as db
from keyboards import (
    admin_main_kb, main_menu_kb, approve_reject_kb,
    difficulty_kb, submit_category_kb, delete_confirm_kb,
)
from config import ADMIN_IDS, DEFAULT_CATEGORIES

router = Router()
                                                                                              # ─── ADMIN CHECK ─────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS                
                                               # ─── STATES ──────────────────────────────────────────────────────────────────               
class AdminAddQ(StatesGroup):                      category    = State()
    question_type = State()
    question    = State()                          option_a    = State()
    option_b    = State()
    option_c    = State()
    option_d    = State()                          option_e    = State()  # NEW
    option_f    = State()  # NEW                   correct     = State()
    difficulty  = State()
    context     = State()
    image       = State()
    confirm     = State()


class AdminDeleteQ(StatesGroup):                   search      = State()
    confirm     = State()                                                                     
class UserSubmitQ(StatesGroup):
    category    = State()
    question    = State()                          option_a    = State()
    option_b    = State()
    option_c    = State()
    option_d    = State()                          correct     = State()
    confirm     = State()                      

# ─── ADMIN PANEL ─────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):             await message.answer("⛔ Рұқсат жоқ.")
        return
    await state.clear()                            total_q = await db.get_question_count()        pending = await db.get_pending_questions(limit=100)
    await message.answer(                              f"🛠 *Админ панелі*\n\n"
        f"📚 Жалпы сұрақтар: *{total_q}*\n"            f"⏳ Кезекте: *{len(pending)}* сұрақ",
        reply_markup=admin_main_kb(),
    )


@router.message(F.text == "🔙 Шығу")
async def exit_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Негізгі мәзір 👇", reply_markup=main_menu_kb())
                                                                                              @router.callback_query(F.data == "show_global_settings")
async def show_global_settings_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)                                      return                                 
    settings = await db.get_bot_settings()     
    time_text = f"{settings['default_time_limit']}с" if settings['default_time_limit'] > 0 else "∞"

    text = (
        f"🌐 *Глобалды баптаулар*\n\n"
        f"📝 Әдепкі сұрақтар саны: *{settings['default_questions_count']}*\n"
        f"⏱ Әдепкі уақыт лимиті: *{time_text}*\n"
        f"🔢 Макс жауап опциялары: *{settings['max_answer_options']}*\n"
        f"✅ Макс дұрыс жауаптар: *{settings['max_correct_answers']}*\n\n"
        f"_Өзгерту үшін төмендегі батырманы бас 👇_"
    )                                          
    from keyboards import global_settings_kb       await callback.message.edit_text(text, reply_markup=global_settings_kb())                 

@router.callback_query(F.data == "show_category_mgmt")
async def show_category_mgmt_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)                                      return
                                                   categories = await db.get_categories()     
    text = (                                           f"📂 *Санаттар басқару*\n\n"                   f"Жалпы санаттар: *{len(categories)}*\n\n"
        f"Не істегіңіз келеді?"                    )
                                                   from keyboards import category_management_kb
    await callback.message.edit_text(text, reply_markup=category_management_kb())
                                               
@router.callback_query(F.data == "show_variant_mgmt")
async def show_variant_mgmt_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)                                      return

    variants = await db.get_variants()
                                                   text = (
        f"📋 *Нұсқалар басқару*\n\n"
        f"Жалпы нұсқалар: *{len(variants)}*\n\n"
        f"Не істегіңіз келеді?"
    )                                          
    from keyboards import variant_management_kb    await callback.message.edit_text(text, reply_markup=variant_management_kb())              
                                               # ─── PENDING REVIEW ──────────────────────────────────────────────────────────               
@router.message(F.text == "📋 Кезектегі сұрақтар")
async def list_pending(message: Message):          if not is_admin(message.from_user.id):
        return
    pendings = await db.get_pending_questions(limit=5)                                            if not pendings:
        await message.answer("✅ Кезекте сұрақ жоқ.")
        return                                 
    for p in pendings:
        text = (
            f"⏳ *Жіберген:* id={p['submitted_by']}\n"
            f"📂 *Категория:* {p['category']}\n"
            f"❓ *Сұрақ:* {p['question']}\n\n"             f"A) {p['option_a']}\n"
            f"B) {p['option_b']}\n"
            f"C) {p['option_c']}\n"
            f"D) {p['option_d']}\n\n"                      f"✅ Дұрыс жауап: *{p['correct']}*\n"                                                         f"🎚 Деңгей: {p['difficulty']}"
        )
        await message.answer(
            text,
            reply_markup=approve_reject_kb(p["id"]),                                                  )
                                               
@router.callback_query(F.data.startswith("approve:"))
async def approve_question(callback: CallbackQuery):                                              if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)
        return
    pending_id = int(callback.data.split(":")[1])
    success = await db.approve_pending(pending_id, callback.from_user.id)
    if success:
        await callback.message.edit_text("✅ Сұрақ бекітілді және базаға қосылды.")
    else:
        await callback.answer("⚠️ Сұрақ табылмады.", show_alert=True)


@router.callback_query(F.data.startswith("reject:"))
async def reject_question(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)
        return                                     pending_id = int(callback.data.split(":")[1])                                                 await db.reject_pending(pending_id, callback.from_user.id)
    await callback.message.edit_text("❌ Сұрақ қабылданбады.")                                
                                               # ─── ADMIN ADD QUESTION ───────────────────────────────────────────────────────

@router.message(F.text == "➕ Сұрақ қосу")     async def admin_add_start(message: Message, state: FSMContext):                                   if not is_admin(message.from_user.id):
        return                                     await state.set_state(AdminAddQ.category)
                                                   await message.answer(
        "📂 *Категория таңда:*",
        reply_markup=submit_category_kb(DEFAULT_CATEGORIES),                                      )
                                               
@router.callback_query(AdminAddQ.category, F.data.startswith("submit_cat:"))
async def admin_add_category(callback: CallbackQuery, state: FSMContext):                         cat = callback.data.split(":", 1)[1]
    await state.update_data(category=cat)

    # Check if this is a UBT subject               ubt_subjects = await db.get_ubt_subjects()
    is_ubt = any(s['name'] == cat for s in ubt_subjects)
                                                   if is_ubt:
        # UBT subject - ask for question type
        await state.set_state(AdminAddQ.question_type)
        await callback.message.edit_text(
            f"📂 Таңдалды: *{cat}* (ҰБТ пәні)\n\n"
            f"🔢 *Сұрақ түрін таңда:*\n\n"                 f"• *single* — бір дұрыс жауап (1 балл)\n"                                                    f"• *context* — мәнмәтін бойынша (2 балл)\n"
            f"• *matching* — сәйкестік (2 балл)\n"                                                        f"• *multiple* — бірнеше жауап (2 балл)",                                                     reply_markup=question_type_kb()
        )
    else:
        # Regular quiz question
        await state.update_data(question_type='single', points=1)                                     await state.set_state(AdminAddQ.question)                                                     await callback.message.edit_text(f"📂 Таңдалды: *{cat}*\n\n❓ Сұрақты жаз:")          

@router.callback_query(AdminAddQ.question_type, F.data.startswith("qtype:"))                  async def admin_add_question_type(callback: CallbackQuery, state: FSMContext):
    qtype = callback.data.split(":")[1]            points = 1 if qtype == "single" else 2     
    await state.update_data(question_type=qtype, points=points)
    await state.set_state(AdminAddQ.question)  
    await callback.message.edit_text(                  f"✅ Түрі: *{qtype}* ({points} балл)\n\n"                                                     f"❓ Сұрақты жаз:"                         )

                                               @router.message(AdminAddQ.question)            async def admin_add_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text)                                                await state.set_state(AdminAddQ.option_a)
    await message.answer("A) жауап нұсқасын жаз:")
                                               
@router.message(AdminAddQ.option_a)
async def admin_add_a(message: Message, state: FSMContext):                                       await state.update_data(option_a=message.text)
    await state.set_state(AdminAddQ.option_b)
    await message.answer("B) жауап нұсқасын жаз:")

                                               @router.message(AdminAddQ.option_b)
async def admin_add_b(message: Message, state: FSMContext):
    await state.update_data(option_b=message.text)                                                await state.set_state(AdminAddQ.option_c)
    await message.answer("C) жауап нұсқасын жаз:")                                                                                           
@router.message(AdminAddQ.option_c)
async def admin_add_c(message: Message, state: FSMContext):                                       await state.update_data(option_c=message.text)
    await state.set_state(AdminAddQ.option_d)      await message.answer("D) жауап нұсқасын жаз:")
                                               
@router.message(AdminAddQ.option_d)
async def admin_add_d(message: Message, state: FSMContext):
    await state.update_data(option_d=message.text)                                                                                               # Check bot settings for max options
    settings = await db.get_bot_settings()
    max_options = settings.get("max_answer_options", 4)

    if max_options >= 5:                               await state.set_state(AdminAddQ.option_e)                                                     await message.answer("E) нұсқасын жазыңыз (немесе /skip өткізіп жіберу):")
    else:                                              await state.set_state(AdminAddQ.correct)                                                      await message.answer("✅ Дұрыс жауапты таңда (A / B / C / D):")                       
                                               @router.message(AdminAddQ.option_e, F.text == "/skip")                                        async def admin_skip_e(message: Message, state: FSMContext):                                      await state.update_data(option_e=None)         await state.set_state(AdminAddQ.correct)                                                      settings = await db.get_bot_settings()         max_options = settings.get("max_answer_options", 4)
    letters = " / ".join(["A", "B", "C", "D"][:max_options])                                  
    await message.answer(f"✅ Дұрыс жауапты таңда ({letters}):")                              
                                               @router.message(AdminAddQ.option_e)
async def admin_add_e(message: Message, state: FSMContext):
    await state.update_data(option_e=message.text)
                                                   # Check if F needed
    settings = await db.get_bot_settings()         max_options = settings.get("max_answer_options", 4)                                       
    if max_options >= 6:                               await state.set_state(AdminAddQ.option_f)                                                     await message.answer("F) нұсқасын жазыңыз (немесе /skip өткізіп жіберу):")
    else:
        await state.set_state(AdminAddQ.correct)
        await message.answer("✅ Дұрыс жауапты таңда (A / B / C / D / E):")                   

@router.message(AdminAddQ.option_f, F.text == "/skip")
async def admin_skip_f(message: Message, state: FSMContext):                                      await state.update_data(option_f=None)
    await state.set_state(AdminAddQ.correct)   
    data = await state.get_data()
    letters = ["A", "B", "C", "D"]
    if data.get("option_e"):
        letters.append("E")                                                                       await message.answer(f"✅ Дұрыс жауапты таңда ({' / '.join(letters)}):")

                                               @router.message(AdminAddQ.option_f)
async def admin_add_f(message: Message, state: FSMContext):
    await state.update_data(option_f=message.text)                                                await state.set_state(AdminAddQ.correct)       await message.answer("✅ Дұрыс жауапты таңда (A / B / C / D / E / F):")                   

@router.message(AdminAddQ.correct)
async def admin_add_correct(message: Message, state: FSMContext):                                 answer = message.text.upper().strip()
    data = await state.get_data()
                                                   # Build valid letters                          valid = ["A", "B", "C", "D"]
    if data.get("option_e"):
        valid.append("E")
    if data.get("option_f"):                           valid.append("F")                                                                         # Check if multiple answers (for max_correct_answers)
    settings = await db.get_bot_settings()         max_correct = settings.get("max_correct_answers", 1)
                                                   if max_correct > 1:
        # Allow comma-separated (A,B,C)                answers = [a.strip() for a in answer.split(",")]
                                                       if not all(a in valid for a in answers):                                                          await message.answer(f"⚠️ Тек {', '.join(valid)} жазыңыз!")                                    return
                                                       if len(answers) > max_correct:                     await message.answer(f"⚠️ Макс {max_correct} дұрыс жауап!")                                    return                             
        await state.update_data(correct=",".join(answers))
    else:                                              # Single answer
        if answer not in valid:
            await message.answer(f"⚠️ {', '.join(valid)} ішінен таңдаңыз!")
            return                                                                                    await state.update_data(correct=answer)

    await state.set_state(AdminAddQ.difficulty)    await message.answer("🎚 Қиындық деңгейін таңда:", reply_markup=difficulty_kb())


@router.callback_query(AdminAddQ.difficulty, F.data.startswith("diff:"))
async def admin_add_difficulty(callback: CallbackQuery, state: FSMContext):
    diff = callback.data.split(":")[1]
    await state.update_data(difficulty=diff, added_by=callback.from_user.id, approved=1)                                                         await state.set_state(AdminAddQ.context)
    await callback.message.edit_text(
        f"🎚 Қиындық: *{diff}*\n\n"                     f"💬 *Мәнмәтін қосу (міндетті емес)*\n\n"                                                     f"Сұраққа қосымша түсініктеме немесе контекст жазыңыз.\n\n"                                   f"Өткізіп жіберу үшін: /skip"
    )
                                                                                              @router.message(AdminAddQ.context, F.text == "/skip")
async def admin_skip_context(message: Message, state: FSMContext):
    await state.update_data(context_text=None)
    await state.set_state(AdminAddQ.image)         await message.answer(                              "🖼 *Сурет қосу (міндетті емес)*\n\n"
        "Сұраққа сурет URL жіберіңіз немесе өткізіп жіберіңіз.\n\n"                                   "Өткізіп жіберу үшін: /skip"               )

                                               @router.message(AdminAddQ.context)             async def admin_add_context(message: Message, state: FSMContext):
    await state.update_data(context_text=message.text)                                            await state.set_state(AdminAddQ.image)
    await message.answer(
        "✅ Мәнмәтін сақталды.\n\n"
        "🖼 *Сурет қосу (міндетті емес)*\n\n"           "Сурет URL жіберіңіз:\n\n"
        "Өткізіп жіберу үшін: /skip"
    )                                          
                                               @router.message(AdminAddQ.image, F.text == "/skip")                                           async def admin_skip_image(message: Message, state: FSMContext):                                  await state.update_data(image_url=None)
    await show_preview(message, state)
                                               
@router.message(AdminAddQ.image, F.photo)
async def admin_add_image_photo(message: Message, state: FSMContext):
    """Handle photo upload."""
    # Get the largest photo
    photo = message.photo[-1]                      file_id = photo.file_id
                                                   # Get file info to build URL                   file = await message.bot.get_file(file_id)     file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"

    await state.update_data(image_url=file_url, image_file_id=file_id)
    await message.answer("✅ Сурет сақталды!")
    await show_preview(message, state)         
                                               @router.message(AdminAddQ.image)
async def admin_add_image_url(message: Message, state: FSMContext):
    """Handle URL or text."""                      url = message.text.strip()
                                                   # Basic URL validation
    if url.startswith(("http://", "https://")):        await state.update_data(image_url=url)
        await message.answer("✅ Сурет URL сақталды.")
        await show_preview(message, state)
    else:                                              await message.answer(
            "⚠️ Дұрыс URL жазыңыз (http:// немесе https://)\n"
            "немесе суретті жүктеңіз\n"                    "немесе /skip басыңыз."
        )

                                               async def show_preview(message: Message, state: FSMContext):                                      """Show question preview before saving."""
    data = await state.get_data()              
    context_part = f"\n💬 Мәнмәтін: _{data.get('context_text', 'жоқ')}_" if data.get('context_text') else ""                                     image_part = f"\n🖼 Сурет: {data.get('image_url', 'жоқ')}" if data.get('image_url') else ""

    # Build options
    options_text = (
        f"A) {data['option_a']}\n"
        f"B) {data['option_b']}\n"                     f"C) {data['option_c']}\n"
        f"D) {data['option_d']}\n"
    )                                                                                             if data.get('option_e'):                           options_text += f"E) {data['option_e']}\n"
    if data.get('option_f'):
        options_text += f"F) {data['option_f']}\n"
                                                   preview = (                                        f"📋 *Сұрақ алдын ала:*\n\n"                   f"📂 {data['category']} | 🎚 {data['difficulty']}\n"                                           f"❓ {data['question']}\n\n"                   f"{options_text}\n"
        f"✅ Дұрыс: *{data['correct']}*"               f"{context_part}"
        f"{image_part}\n\n"
        f"Сақтау үшін /save, болдырмау үшін /cancel"                                              )
    await message.answer(preview)
    await state.set_state(AdminAddQ.confirm)   

@router.message(AdminAddQ.confirm, F.text == "/save")
async def admin_save_question(message: Message, state: FSMContext):                               data = await state.get_data()
    q_id = await db.add_question(data)             await state.clear()
    await message.answer(                              f"✅ Сұрақ базаға сақталды! (ID: {q_id})",
        reply_markup=admin_main_kb(),
    )


@router.message(AdminAddQ.confirm, F.text == "/cancel")                                       @router.message(AdminAddQ.question, F.text == "/cancel")
async def admin_cancel(message: Message, state: FSMContext):                                      await state.clear()
    await message.answer("❌ Болдырылмады.", reply_markup=admin_main_kb())


# ─── DELETE QUESTION ──────────────────────────────────────────────────────────              
@router.message(F.text == "🗑 Сұрақ өшіру")     async def admin_delete_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(AdminDeleteQ.search)
    await message.answer(                              "🔍 *Сұрақ іздеу*\n\n"
        "Сұрақтың ID нөмірін немесе кілт сөзін жаз.\n"
        "Мысалы: `123` немесе `Қазақстан`\n\n"
        "Болдырмау үшін /cancel",                      reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AdminDeleteQ.search, F.text == "/cancel")                                     async def admin_delete_cancel(message: Message, state: FSMContext):
    await state.clear()                            await message.answer("❌ Болдырылмады.", reply_markup=admin_main_kb())                    
                                               @router.message(AdminDeleteQ.search)
async def admin_delete_search(message: Message, state: FSMContext):
    query = message.text.strip()

    # Check if it's a numeric ID
    if query.isdigit():
        q_id = int(query)                              async with aiosqlite.connect(db.DB_PATH) as database:
            database.row_factory = aiosqlite.Row                                                          async with database.execute(
                "SELECT * FROM questions WHERE id=?", (q_id,)
            ) as cur:                                          row = await cur.fetchone()

        if not row:                                        await message.answer(
                f"⚠️ ID {q_id} табылмады.\n"                    "Басқа ID немесе кілт сөз жаз, немесе /cancel"                                            )
            return                             
        q = dict(row)                                  await show_delete_confirm(message, state, q)

    else:
        # Keyword search
        results = await db.search_questions(query, limit=10)
                                                       if not results:
            await message.answer(                              f"⚠️ *'{query}'* бойынша сұрақ табылмады.\n"
                "Басқа кілт сөз жаз немесе /cancel"                                                       )
            return

        if len(results) == 1:
            await show_delete_confirm(message, state, results[0])
        else:                                              lines = [f"🔍 *Табылды: {len(results)} сұрақ*\n"]
            for q in results[:5]:
                lines.append(                                      f"• `{q['id']}` — {q['question'][:50]}{'...' if len(q['question']) > 50 else ''}"                                                        )
            if len(results) > 5:                               lines.append(f"\n_...және тағы {len(results)-5} сұрақ_")                      
            lines.append("\n💡 Нақты ID нөмірін жаз, мысалы: `123`")                                      await message.answer("\n".join(lines))


async def show_delete_confirm(message: Message, state: FSMContext, q: dict):                      await state.update_data(question_id=q["id"])
    await state.set_state(AdminDeleteQ.confirm)

    text = (
        f"🗑 *Сұрақты өшіргіңіз келе ме?*\n\n"          f"📋 *ID:* {q['id']}\n"
        f"📂 *Категория:* {q['category']}\n"           f"❓ *Сұрақ:* {q['question']}\n\n"
        f"A) {q['option_a']}\n"                        f"B) {q['option_b']}\n"
        f"C) {q['option_c']}\n"
        f"D) {q['option_d']}\n\n"
        f"✅ Дұрыс: *{q['correct']}*"
    )                                              await message.answer(text, reply_markup=delete_confirm_kb(q["id"]))
                                                                                              @router.callback_query(AdminDeleteQ.confirm, F.data.startswith("delconfirm:"))
async def admin_delete_confirmed(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)
        return
                                                   data = await state.get_data()
    q_id = data.get("question_id")             
    if not q_id:
        await callback.answer("⚠️ Қате: ID табылмады", show_alert=True)                                return

    success = await db.delete_question(q_id)   
    if success:
        await callback.message.edit_text(                  f"✅ Сұрақ #{q_id} сәтті өшірілді!"
        )                                              await callback.message.answer(
            "Басқа сұрақ өшіру үшін: 🗑 Сұрақ өшіру",
            reply_markup=admin_main_kb(),              )
    else:
        await callback.message.edit_text("⚠️ Сұрақ табылмады (мүмкін бұрын өшірілген)")

    await state.clear()

                                               @router.callback_query(AdminDeleteQ.confirm, F.data == "delcancel")                           async def admin_delete_cancelled(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Өшіру болдырылмады.")
    await callback.message.answer("Админ панелі 👇", reply_markup=admin_main_kb())
                                               
# ─── USER SUBMIT QUESTION ─────────────────────────────────────────────────────              
@router.message(F.text == "💡 Сұрақ ұсыну")    async def user_submit_start(message: Message, state: FSMContext):
    await state.clear()                            await state.set_state(UserSubmitQ.category)
    await message.answer(
        "💡 *Сұрақ жіберу*\n\n"
        "Сенің сұрағың администратор тексергеннен кейін базаға қосылады.\n\n"
        "📂 *Категория таңда:*",
        reply_markup=submit_category_kb(DEFAULT_CATEGORIES),
    )


@router.callback_query(UserSubmitQ.category, F.data.startswith("submit_cat:"))
async def user_submit_category(callback: CallbackQuery, state: FSMContext):
    cat = callback.data.split(":", 1)[1]           await state.update_data(category=cat)
    await state.set_state(UserSubmitQ.question)    await callback.message.edit_text(f"📂 Таңдалды: *{cat}*\n\n❓ Сұрақты жаз:")                                                             
@router.message(UserSubmitQ.question)
async def user_submit_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await state.set_state(UserSubmitQ.option_a)
    await message.answer("A) жауап нұсқасын жаз:")
                                                                                              @router.message(UserSubmitQ.option_a)          async def user_submit_a(message: Message, state: FSMContext):                                     await state.update_data(option_a=message.text)                                                await state.set_state(UserSubmitQ.option_b)
    await message.answer("B) жауап нұсқасын жаз:")


@router.message(UserSubmitQ.option_b)
async def user_submit_b(message: Message, state: FSMContext):
    await state.update_data(option_b=message.text)                                                await state.set_state(UserSubmitQ.option_c)
    await message.answer("C) жауап нұсқасын жаз:")

                                               @router.message(UserSubmitQ.option_c)
async def user_submit_c(message: Message, state: FSMContext):
    await state.update_data(option_c=message.text)
    await state.set_state(UserSubmitQ.option_d)
    await message.answer("D) жауап нұсқасын жаз:")                                                                                                                                          @router.message(UserSubmitQ.option_d)
async def user_submit_d(message: Message, state: FSMContext):                                     await state.update_data(option_d=message.text)                                                await state.set_state(UserSubmitQ.correct)     await message.answer("✅ Дұрыс жауапты жаз (A / B / C / D):")
                                               
@router.message(UserSubmitQ.correct, F.text.upper().in_({"A", "B", "C", "D"}))
async def user_submit_correct(message: Message, state: FSMContext):
    await state.update_data(correct=message.text.upper())
    data = await state.get_data()

    preview = (
        f"📋 *Сұрағыңның алдын алауы:*\n\n"            f"📂 {data['category']}\n"                     f"❓ {data['question']}\n\n"
        f"A) {data['option_a']}\n"                     f"B) {data['option_b']}\n"
        f"C) {data['option_c']}\n"                     f"D) {data['option_d']}\n\n"
        f"✅ Дұрыс: *{data['correct']}*\n\n"
        f"Жіберу үшін /send, болдырмау үшін /cancel"
    )
    await message.answer(preview)
    await state.set_state(UserSubmitQ.confirm) 

@router.message(UserSubmitQ.confirm, F.text == "/send")
async def user_send_question(message: Message, state: FSMContext):                                data = await state.get_data()                  await db.submit_question(message.from_user.id, data)
    await state.clear()
    await message.answer(
        "✅ *Сұрағыңыз жіберілді!*\n"
        "Администратор тексеріп, базаға қосады.\n"
        "Рахмет! 🙏",
        reply_markup=main_menu_kb(),
    )
                                               
@router.message(UserSubmitQ.confirm, F.text == "/cancel")
async def user_cancel_submit(message: Message, state: FSMContext):
    await state.clear()                            await message.answer("❌ Болдырылмады.", reply_markup=main_menu_kb())                     
                                               # ─── ADMIN STATS ─────────────────────────────────────────────────────────────
                                               @router.message(F.text == "📊 Бот статистикасы")                                              async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):             return
    total_q = await db.get_question_count()        pending = await db.get_pending_questions(100)
    cats = await db.get_categories()
                                                   cat_lines = "\n".join([f"  • {c}: {n}" for c, n in cats]) or "  —"                        
    await message.answer(                              f"📊 *Бот статистикасы*\n\n"
        f"📚 Жалпы сұрақтар: *{total_q}*\n"            f"⏳ Кезекте: *{len(pending)}*\n\n"
        f"📂 *Категориялар:*\n{cat_lines}",
        reply_markup=admin_main_kb(),              )
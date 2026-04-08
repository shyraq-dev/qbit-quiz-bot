from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove                         from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio                                 
import database as db
from keyboards import admin_main_kb, broadcast_target_kb, broadcast_type_kb
from config import ADMIN_IDS
                                               router = Router()
                                               
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS                                                               
def replace_variables(text: str, user_id: int, username: str, full_name: str, lang: str) -> str:                                                 """Replace variables in broadcast text."""     from datetime import datetime
                                                   now = datetime.now()

    # Parse name
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0] if name_parts else "Қолданушы"
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    # Weekday names in Kazakh
    weekdays = ["Дүйсенбі", "Сейсенбі", "Сәрсенбі", "Бейсенбі", "Жұма", "Сенбі", "Жексенбі"]      weekday = weekdays[now.weekday()]
                                                   replacements = {
        "{ID}": str(user_id),                          "{NAME}": first_name,
        "{SURNAME}": last_name,
        "{NAMESURNAME}": full_name,                    "{USERNAME}": f"@{username}" if username else "жоқ",                                          "{LANG}": lang or "kk",
        "{DATE}": now.strftime("%Y-%m-%d"),            "{TIME}": now.strftime("%H:%M"),
        "{WEEKDAY}": weekday,                          "{MENTION}": f"<a href='tg://user?id={user_id}'>{first_name}</a>",                        }

    for key, value in replacements.items():            text = text.replace(key, value)
                                                   return text
                                                                                              class BroadcastState(StatesGroup):
    choosing_type = State()
    choosing_target = State()
    entering_text = State()                        entering_media = State()
    confirm = State()
                                               
@router.message(F.text == "📩 Хат жіберу")
async def broadcast_menu(message: Message, state: FSMContext):                                    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await state.set_state(BroadcastState.choosing_type)
                                                   await message.answer(
        "📩 *Хат жіберу*\n\n"
        "Қандай түрде жіберасіз?",                     reply_markup=broadcast_type_kb()
    )
                                               
@router.callback_query(BroadcastState.choosing_type, F.data.startswith("bcast_type:"))
async def broadcast_type_chosen(callback: CallbackQuery, state: FSMContext):
    msg_type = callback.data.split(":")[1]  # text, photo, video, document                    
    await state.update_data(message_type=msg_type)
    await state.set_state(BroadcastState.choosing_target)                                     
    # Get user counts
    all_count = len(await db.get_all_user_ids())
    active_count = len(await db.get_active_user_ids(days=7))                                  
    await callback.message.edit_text(
        f"📩 *Хат жіберу*\n\n"
        f"Түрі: *{msg_type}*\n\n"
        f"Кімге жіберу керек?\n\n"
        f"👥 Барлығы: {all_count} қолданушы\n"
        f"✅ Белсенділер (7 күн): {active_count} қолданушы",
        reply_markup=broadcast_target_kb()         )

                                               @router.callback_query(BroadcastState.choosing_target, F.data.startswith("bcast_target:"))
async def broadcast_target_chosen(callback: CallbackQuery, state: FSMContext):                    target = callback.data.split(":")[1]  # all, active                                       
    await state.update_data(target_type=target)
    await state.set_state(BroadcastState.entering_text)
                                                   data = await state.get_data()
    msg_type = data.get("message_type", "text")

    if msg_type == "text":
        text = (
            "📝 *Хабарлама мәтінін жазыңыз:*\n\n"
            "Markdown қолдау бар (bold, italic, code)\n\n"
            "Болдырмау үшін /cancel"
        )
    else:
        text = (
            f"📝 *{msg_type.upper()} үшін caption жазыңыз:*\n\n"
            "Болдырмау үшін /cancel"                   )
                                                   await callback.message.edit_text(text)


@router.message(BroadcastState.entering_text, F.text == "/cancel")
async def broadcast_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Болдырылмады.", reply_markup=admin_main_kb())
                                               
@router.message(BroadcastState.entering_text)
async def broadcast_text_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    msg_type = data.get("message_type", "text")

    await state.update_data(message_text=message.text)                                        
    if msg_type != "text":
        await state.set_state(BroadcastState.entering_media)
        await message.answer(                              f"🔗 *{msg_type.upper()} URL жіберіңіз:*\n\n"
            "Мысалы: https://example.com/image.jpg\n\n"                                                   "Болдырмау үшін /cancel"
        )
    else:
        # Show formatting help before preview          help_text = (
            "📝 *Пішімдеу және айнымалылар:*\n\n"
            "*HTML теглер:*\n"
            "<b>қалың</b> — қалың\n"
            "<i>көлбеу</i> — көлбеу\n"                     "<u>астын сызу</u> — астын сызу\n"             "<s>үстін сызу</s> — сызылған\n"
            "<code>код</code> — код\n"
            "<pre>блок</pre> — код блогы\n"                "<a href='url'>сілтеме</a> — сілтеме\n\n"                                                     "*Айнымалылар:*\n"
            "{ID} — қолданушы ID\n"                        "{NAME} — аты\n"                               "{SURNAME} — тегі\n"
            "{NAMESURNAME} — толық аты\n"                  "{USERNAME} — @username\n"
            "{LANG} — тілі\n"
            "{DATE} — күн (2026-02-23)\n"
            "{TIME} — уақыт (15:30)\n"
            "{WEEKDAY} — апта күні\n"                      "{MENTION} — mention сілтеме\n\n"
            "_Мысалы:_ <b>Сәлем, {NAME}!</b>"
        )
        await message.answer(help_text)

        await show_broadcast_preview(message, state)
                                                                                              @router.message(BroadcastState.entering_media, F.text == "/cancel")
async def broadcast_media_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Болдырылмады.", reply_markup=admin_main_kb())                    
                                               @router.message(BroadcastState.entering_media, F.photo)
async def broadcast_photo_uploaded(message: Message, state: FSMContext):                          """Handle photo upload."""
    photo = message.photo[-1]
    file_id = photo.file_id
                                                   # Get file URL
    file = await message.bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"

    await state.update_data(media_url=file_url, media_file_id=file_id)                            await message.answer("✅ Сурет жүктелді!")
    await show_broadcast_preview(message, state)                                              
                                               @router.message(BroadcastState.entering_media, F.video)                                       async def broadcast_video_uploaded(message: Message, state: FSMContext):
    """Handle video upload."""
    video = message.video
    file_id = video.file_id

    file = await message.bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"

    await state.update_data(media_url=file_url, media_file_id=file_id)
    await message.answer("✅ Видео жүктелді!")
    await show_broadcast_preview(message, state)                                              

@router.message(BroadcastState.entering_media, F.document)                                    async def broadcast_document_uploaded(message: Message, state: FSMContext):                       """Handle document upload."""
    doc = message.document                         file_id = doc.file_id
                                                   file = await message.bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"       
    await state.update_data(media_url=file_url, media_file_id=file_id)                            await message.answer("✅ Файл жүктелді!")
    await show_broadcast_preview(message, state)                                              

@router.message(BroadcastState.entering_media)
async def broadcast_media_entered(message: Message, state: FSMContext):
    """Handle URL (fallback)."""
    url = message.text.strip()                 
    if not url.startswith(("http://", "https://")):
        await message.answer(                              "⚠️ Файл жүктеңіз (сурет/видео/документ)\n"
            "немесе дұрыс URL жазыңыз (http://...)\n\n"
            "/cancel — болдырмау"                      )                                              return                                 
    await state.update_data(media_url=url)
    await show_broadcast_preview(message, state)
                                               
async def show_broadcast_preview(message: Message, state: FSMContext):
    """Show broadcast preview before sending."""
    data = await state.get_data()

    msg_type = data.get("message_type", "text")
    target = data.get("target_type", "all")
    msg_text = data.get("message_text", "")        media_url = data.get("media_url", "")
                                                   # Get target count
    if target == "all":
        user_ids = await db.get_all_user_ids()         target_text = "Барлық қолданушылар"
    else:                                              user_ids = await db.get_active_user_ids(days=7)
        target_text = "Белсенділер (7 күн)"

    await state.update_data(user_ids=user_ids)

    preview = (
        f"📋 *Алдын ала қарау:*\n\n"
        f"📩 Түрі: {msg_type}\n"                       f"👥 Алушылар: {target_text} ({len(user_ids)})\n\n"
        f"💬 Мәтін:\n_{msg_text[:100]}{'...' if len(msg_text) > 100 else ''}_\n"                  )
                                                   if media_url:
        preview += f"\n🔗 Media: {media_url[:50]}...\n"
                                                   preview += "\n✅ Жіберу үшін /send\n❌ Болдырмау үшін /cancel"

    await message.answer(preview)                  await state.set_state(BroadcastState.confirm)                                             

@router.message(BroadcastState.confirm, F.text == "/cancel")
async def broadcast_confirm_cancel(message: Message, state: FSMContext):                          await state.clear()                            await message.answer("❌ Болдырылмады.", reply_markup=admin_main_kb())
                                                                                              @router.message(BroadcastState.confirm, F.text == "/send")
async def broadcast_send(message: Message, state: FSMContext):
    data = await state.get_data()              
    user_ids = data.get("user_ids", [])
    msg_type = data.get("message_type", "text")    msg_text = data.get("message_text", "")
    media_url = data.get("media_url", "")
    target_type = data.get("target_type", "all")
    admin_id = message.from_user.id
                                                   # Create broadcast record
    broadcast_id = await db.create_broadcast(
        admin_id=admin_id,
        message_text=msg_text,
        message_type=msg_type,
        media_url=media_url,                           target_type=target_type,                       total_users=len(user_ids)
    )                                          
    await state.clear()

    status_msg = await message.answer(                 f"📤 *Жіберілуде...*\n\n"                      f"Жалпы: {len(user_ids)}\n"
        f"Жіберілді: 0\n"
        f"Қате: 0",
        reply_markup=admin_main_kb()
    )

    # Send to all users
    sent = 0
    failed = 0                                 
    media_file_id = data.get("media_file_id")  # If uploaded                                  
    for i, user_id in enumerate(user_ids):
        try:                                               # Get user info for variables
            user_info = await db.get_user_by_id(user_id)
            username = user_info.get("username", "") if user_info else ""
            full_name = user_info.get("full_name", "Қолданушы") if user_info else "Қолданушы"
            lang = user_info.get("language_code", "kk") if user_info else "kk"

            # Replace variables
            personalized_text = replace_variables(msg_text, user_id, username, full_name, lang)                                              
            if msg_type == "text":
                await message.bot.send_message(                    user_id,
                    personalized_text,
                    parse_mode="HTML"
                )                                          elif msg_type == "photo":
                if media_file_id:
                    await message.bot.send_photo(
                        user_id,
                        media_file_id,
                        caption=personalized_text,
                        parse_mode="HTML"
                    )                                          else:
                    from aiogram.types import URLInputFile
                    photo = URLInputFile(media_url)
                    await message.bot.send_photo(
                        user_id,
                        photo,
                        caption=personalized_text,                                                                    parse_mode="HTML"
                    )                                      elif msg_type == "video":
                if media_file_id:
                    await message.bot.send_video(                                                                     user_id,
                        media_file_id,
                        caption=personalized_text,
                        parse_mode="HTML"
                    )                                          else:
                    from aiogram.types import URLInputFile
                    video = URLInputFile(media_url)
                    await message.bot.send_video(                                                                     user_id,
                        video,                                         caption=personalized_text,                                                                    parse_mode="HTML"
                    )
            elif msg_type == "document":
                if media_file_id:                                  await message.bot.send_document(
                        user_id,
                        media_file_id,                                 caption=personalized_text,                                                                    parse_mode="HTML"
                    )
                else:
                    from aiogram.types import URLInputFile
                    doc = URLInputFile(media_url)
                    await message.bot.send_document(
                        user_id,
                        doc,
                        caption=personalized_text,
                        parse_mode="HTML"
                    )

            sent += 1
        except Exception as e:                             failed += 1
                                                       # Update status every 10 users
        if (i + 1) % 10 == 0 or (i + 1) == len(user_ids):
            try:
                await status_msg.edit_text(
                    f"📤 *Жіберілуде...*\n\n"                      f"Жалпы: {len(user_ids)}\n"
                    f"Жіберілді: {sent}\n"
                    f"Қате: {failed}"
                )                                          except Exception:
                pass  # Can't edit - skip
                                                       # Small delay to avoid rate limits
        await asyncio.sleep(0.05)
                                                   # Update database
    await db.update_broadcast_stats(broadcast_id, sent, failed)                               
    # Final status
    try:                                               await status_msg.edit_text(
            f"✅ *Жіберу аяқталды!*\n\n"
            f"📊 Нәтиже:\n"                                f"Жалпы: {len(user_ids)}\n"
            f"✅ Жіберілді: {sent}\n"                      f"❌ Қате: {failed}\n\n"
            f"_ID: {broadcast_id}_"                    )
    except Exception:
        # Can't edit - send new message                await message.answer(
            f"✅ *Жіберу аяқталды!*\n\n"
            f"📊 Нәтиже:\n"
            f"Жалпы: {len(user_ids)}\n"                    f"✅ Жіберілді: {sent}\n"
            f"❌ Қате: {failed}\n\n"
            f"_ID: {broadcast_id}_"                    )                                      

@router.message(F.text == "📊 Жіберу тарихы")  async def broadcast_history(message: Message):
    if not is_admin(message.from_user.id):             return                                 
    history = await db.get_broadcast_history(limit=5)                                         
    if not history:
        await message.answer("📭 Әзірше жіберулер жоқ.", reply_markup=admin_main_kb())                return

    lines = ["📊 *Соңғы жіберулер:*\n"]        
    for h in history:
        msg_text = h['message_text'][:30] + "..." if len(h['message_text']) > 30 else h['message_text']
                                                       lines.append(
            f"🆔 {h['id']} | {h['message_type']}\n"                                                       f"💬 _{msg_text}_\n"
            f"👥 {h['sent_count']}/{h['total_users']} (❌ {h['failed_count']})\n"
            f"📅 {h['created_at'][:16]}\n"
        )

    await message.answer("\n".join(lines), reply_markup=admin_main_kb())
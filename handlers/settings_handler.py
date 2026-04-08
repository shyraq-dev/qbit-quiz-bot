from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
                                               import database as db
from keyboards import (                            settings_menu_kb, global_settings_kb, main_menu_kb,                                           user_settings_kb, admin_main_kb,           )
from config import ADMIN_IDS                   
router = Router()                              

def is_admin(user_id: int) -> bool:                return user_id in ADMIN_IDS

                                               # ─── ADMIN GLOBAL SETTINGS ────────────────────────────────────────────────────              
@router.message(F.text == "⚙️ Баптаулар")
async def settings_menu(message: Message):         if is_admin(message.from_user.id):                 # Admin sees global settings menu
        await message.answer(                              "⚙️ *Баптаулар*\n\n"                            "Қандай баптауды өзгерткіңіз келеді?",                                                        reply_markup=settings_menu_kb()
        )                                          else:
        # User sees personal settings
        await show_user_settings(message)

                                               @router.message(F.text == "🌐 Глобалды баптаулар")                                            async def show_global_settings(message: Message):
    if not is_admin(message.from_user.id):
        return                                                                                    settings = await db.get_bot_settings()
                                                   time_text = f"{settings['default_time_limit']}с" if settings['default_time_limit'] > 0 else "∞"

    text = (                                           f"🌐 *Глобалды баптаулар*\n\n"                 f"📝 Әдепкі сұрақтар саны: *{settings['default_questions_count']}*\n"
        f"⏱ Әдепкі уақыт лимиті: *{time_text}*\n"
        f"🔢 Макс жауап опциялары: *{settings['max_answer_options']}*\n"                              f"✅ Макс дұрыс жауаптар: *{settings['max_correct_answers']}*\n\n"
        f"_Өзгерту үшін төмендегі батырманы бас 👇_"                                              )
                                                   await message.answer(text, reply_markup=global_settings_kb())                                                                            
@router.callback_query(F.data.startswith("gsetting:"))
async def edit_global_setting(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)
        return
                                                   setting = callback.data.split(":")[1]          settings = await db.get_bot_settings()

    if setting == "questions_count":
        text = (
            f"📝 *Әдепкі сұрақтар саны*\n\n"               f"Қазіргі: *{settings['default_questions_count']}*\n\n"                                       f"Жаңа мәнді таңда:"
        )
        from keyboards import questions_count_kb
        await callback.message.edit_text(text, reply_markup=questions_count_kb("global"))     
    elif setting == "time_limit":                      time_text = f"{settings['default_time_limit']}с" if settings['default_time_limit'] > 0 else "∞"
        text = (                                           f"⏱ *Әдепкі уақыт лимиті*\n\n"                 f"Қазіргі: *{time_text}*\n\n"
            f"Жаңа мәнді таңда:"                       )
        from keyboards import time_limit_kb            await callback.message.edit_text(text, reply_markup=time_limit_kb("global"))

    elif setting == "max_options":                     text = (
            f"🔢 *Макс жауап опциялары*\n\n"               f"Қазіргі: *{settings['max_answer_options']}*\n\n"
            f"Жаңа мәнді таңда:"
        )
        from keyboards import max_options_kb
        await callback.message.edit_text(text, reply_markup=max_options_kb())
                                                   elif setting == "max_correct":
        text = (                                           f"✅ *Макс дұрыс жауаптар*\n\n"
            f"Қазіргі: *{settings['max_correct_answers']}*\n\n"                                           f"Жаңа мәнді таңда:"                       )
        from keyboards import max_correct_kb           await callback.message.edit_text(text, reply_markup=max_correct_kb())                                                                    elif setting == "shuffle":
        sq_text = "✅ Қосулы" if settings['shuffle_questions'] else "❌ Өшірулі"                      sa_text = "✅ Қосулы" if settings['shuffle_answers'] else "❌ Өшірулі"                
        text = (
            f"🎲 *Shuffle режимі*\n\n"
            f"🎲 Сұрақтар араластыру: {sq_text}\n"
            f"🔀 Жауаптар араластыру: {sa_text}\n\n"
            f"_Қандай баптауды өзгерткіңіз келеді?_"
        )
        from keyboards import shuffle_settings_kb
        await callback.message.edit_text(text, reply_markup=shuffle_settings_kb("global"))    
                                               @router.callback_query(F.data.startswith("gset:"))                                            async def save_global_setting(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)
        return                                 
    _, param, value = callback.data.split(":")
    value = int(value)                         
    settings = await db.get_bot_settings()     
    if param == "qcount":
        settings["default_questions_count"] = value
    elif param == "tlimit":
        settings["default_time_limit"] = value
    elif param == "maxopt":
        settings["max_answer_options"] = value     elif param == "maxcorr":                           settings["max_correct_answers"] = value

    await db.update_bot_settings(settings)     
    await callback.answer("✅ Сақталды!", show_alert=True)                                    
    # Show updated settings                        time_text = f"{settings['default_time_limit']}с" if settings['default_time_limit'] > 0 else "∞"

    text = (                                           f"🌐 *Глобалды баптаулар* _(жаңартылды)_\n\n"                                                 f"📝 Әдепкі сұрақтар саны: *{settings['default_questions_count']}*\n"
        f"⏱ Әдепкі уақыт лимиті: *{time_text}*\n"                                                     f"🔢 Макс жауап опциялары: *{settings['max_answer_options']}*\n"
        f"✅ Макс дұрыс жауаптар: *{settings['max_correct_answers']}*"                            )                                                                                             await callback.message.edit_text(text, reply_markup=global_settings_kb())                                                                
@router.callback_query(F.data.startswith("gshuffle:"))
async def edit_global_shuffle_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)
        return

    setting = callback.data.split(":")[1]
    settings = await db.get_bot_settings()
                                                   current = bool(settings.get(f'shuffle_{setting}', 1))                                                                                        title = "🎲 Сұрақтар араластыру" if setting == "questions" else "🔀 Жауаптар араластыру"
    status = "✅ Қосулы" if current else "❌ Өшірулі"

    text = (                                           f"{title}\n\n"                                 f"Қазіргі: {status}\n\n"
        f"_Жаңа күйді таңда:_"                     )                                          
    from keyboards import shuffle_toggle_kb        await callback.message.edit_text(text, reply_markup=shuffle_toggle_kb("global", setting, current))

                                               @router.callback_query(F.data.startswith("gshtoggle:"))
async def save_global_shuffle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)                                      return
                                                   _, setting, value = callback.data.split(":")
    value = int(value)                                                                            settings = await db.get_bot_settings()         settings[f'shuffle_{setting}'] = value     
    await db.update_bot_settings(settings)
    await callback.answer("✅ Сақталды!", show_alert=True)

    # Back to shuffle menu
    sq_text = "✅ Қосулы" if settings['shuffle_questions'] else "❌ Өшірулі"
    sa_text = "✅ Қосулы" if settings['shuffle_answers'] else "❌ Өшірулі"                    
    text = (
        f"🎲 *Shuffle режимі* _(жаңартылды)_\n\n"                                                     f"🎲 Сұрақтар араластыру: {sq_text}\n"
        f"🔀 Жауаптар араластыру: {sa_text}"
    )                                                                                             from keyboards import shuffle_settings_kb      await callback.message.edit_text(text, reply_markup=shuffle_settings_kb("global"))
                                               
@router.callback_query(F.data.startswith("back_shuffle:"))
async def back_to_shuffle_menu(callback: CallbackQuery):                                          scope = callback.data.split(":")[1]
                                                   if scope == "global":                              if not is_admin(callback.from_user.id):
            await callback.answer("⛔ Рұқсат жоқ.", show_alert=True)                                      return

        settings = await db.get_bot_settings()
        sq_text = "✅ Қосулы" if settings['shuffle_questions'] else "❌ Өшірулі"
        sa_text = "✅ Қосулы" if settings['shuffle_answers'] else "❌ Өшірулі"                
        text = (                                           f"🎲 *Shuffle режимі*\n\n"
            f"🎲 Сұрақтар араластыру: {sq_text}\n"                                                        f"🔀 Жауаптар араластыру: {sa_text}"                                                      )
                                                       from keyboards import shuffle_settings_kb                                                     await callback.message.edit_text(text, reply_markup=shuffle_settings_kb("global"))
                                                   else:  # user
        user_id = callback.from_user.id                effective = await db.get_effective_quiz_settings(user_id)                             
        sq_text = "✅ Қосулы" if effective['shuffle_questions'] else "❌ Өшірулі"
        sa_text = "✅ Қосулы" if effective['shuffle_answers'] else "❌ Өшірулі"

        text = (
            f"🎲 *Shuffle режимі*\n\n"                     f"🎲 Сұрақтар араластыру: {sq_text}\n"                                                        f"🔀 Жауаптар араластыру: {sa_text}"
        )                                      
        from keyboards import shuffle_settings_kb                                                     await callback.message.edit_text(text, reply_markup=shuffle_settings_kb("user"))


# ─── USER PERSONAL SETTINGS ───────────────────────────────────────────────────

async def show_user_settings(message: Message):    user_id = message.from_user.id                 effective = await db.get_effective_quiz_settings(user_id)                                     user_custom = await db.get_user_quiz_settings(user_id)
                                                   qcount_custom = user_custom and user_custom["questions_count"]                                tlimit_custom = user_custom and user_custom["time_limit"]                                                                                    qcount_text = f"*{effective['questions_count']}*" + ("" if qcount_custom else " _(әдепкі)_")                                                                                                if effective['time_limit'] == 0:                   tlimit_text = "*∞*"
    else:
        tlimit_text = f"*{effective['time_limit']}с*"
    tlimit_text += "" if tlimit_custom else " _(әдепкі)_"                                                                                        text = (                                           f"⚙️ *Менің баптауларым*\n\n"
        f"📝 Сұрақтар саны: {qcount_text}\n"           f"⏱ Уақыт лимиті: {tlimit_text}\n\n"           f"_Өзгерту үшін төмендегі батырманы бас 👇_"
    )                                          
    await message.answer(text, reply_markup=user_settings_kb())

                                               @router.callback_query(F.data.startswith("usetting:"))
async def edit_user_setting(callback: CallbackQuery):
    setting = callback.data.split(":")[1]
    user_id = callback.from_user.id                effective = await db.get_effective_quiz_settings(user_id)

    if setting == "questions_count":
        text = (
            f"📝 *Сұрақтар саны*\n\n"                      f"Қазіргі: *{effective['questions_count']}*\n\n"
            f"Жаңа мәнді таңда:"                       )
        from keyboards import questions_count_kb
        await callback.message.edit_text(text, reply_markup=questions_count_kb("user"))       
    elif setting == "time_limit":
        time_text = f"{effective['time_limit']}с" if effective['time_limit'] > 0 else "∞"
        text = (
            f"⏱ *Уақыт лимиті*\n\n"
            f"Қазіргі: *{time_text}*\n\n"
            f"Жаңа мәнді таңда:"
        )                                              from keyboards import time_limit_kb
        await callback.message.edit_text(text, reply_markup=time_limit_kb("user"))            
    elif setting == "shuffle":
        sq_text = "✅ Қосулы" if effective['shuffle_questions'] else "❌ Өшірулі"
        sa_text = "✅ Қосулы" if effective['shuffle_answers'] else "❌ Өшірулі"
                                                       text = (
            f"🎲 *Shuffle режимі*\n\n"                     f"🎲 Сұрақтар араластыру: {sq_text}\n"                                                        f"🔀 Жауаптар араластыру: {sa_text}\n\n"
            f"_Қандай баптауды өзгерткіңіз келеді?_"                                                  )                                              from keyboards import shuffle_settings_kb
        await callback.message.edit_text(text, reply_markup=shuffle_settings_kb("user"))      

@router.callback_query(F.data.startswith("uset:"))                                            async def save_user_setting(callback: CallbackQuery):
    _, param, value = callback.data.split(":")     value = int(value)
    user_id = callback.from_user.id

    if param == "qcount":                              await db.update_user_quiz_settings(user_id, questions_count=value)
    elif param == "tlimit":                            await db.update_user_quiz_settings(user_id, time_limit=value)                         
    await callback.answer("✅ Сақталды!", show_alert=True)
                                                   # Show updated settings
    effective = await db.get_effective_quiz_settings(user_id)
                                                   time_text = f"{effective['time_limit']}с" if effective['time_limit'] > 0 else "∞"
                                                   text = (
        f"⚙️ *Менің баптауларым* _(жаңартылды)_\n\n"                                                   f"📝 Сұрақтар саны: *{effective['questions_count']}*\n"
        f"⏱ Уақыт лимиті: *{time_text}*"
    )                                          
    await callback.message.edit_text(text, reply_markup=user_settings_kb())                   
                                               @router.callback_query(F.data == "back_to_settings")                                          async def back_to_settings(callback: CallbackQuery):                                              if is_admin(callback.from_user.id):                await callback.message.edit_text(
            "⚙️ *Баптаулар*\n\n"                            "Қандай баптауды өзгерткіңіз келеді?",                                                        reply_markup=settings_menu_kb()
        )
    else:
        user_id = callback.from_user.id                effective = await db.get_effective_quiz_settings(user_id)

        time_text = f"{effective['time_limit']}с" if effective['time_limit'] > 0 else "∞"                                                            text = (
            f"⚙️ *Менің баптауларым*\n\n"
            f"📝 Сұрақтар саны: *{effective['questions_count']}*\n"                                       f"⏱ Уақыт лимиті: *{time_text}*"
        )                                      
        await callback.message.edit_text(text, reply_markup=user_settings_kb())


@router.callback_query(F.data.startswith("ushuffle:"))
async def edit_user_shuffle_detail(callback: CallbackQuery):
    setting = callback.data.split(":")[1]
    user_id = callback.from_user.id
    effective = await db.get_effective_quiz_settings(user_id)
                                                   current = bool(effective.get(f'shuffle_{setting}', 1))                                    
    title = "🎲 Сұрақтар араластыру" if setting == "questions" else "🔀 Жауаптар араластыру"
    status = "✅ Қосулы" if current else "❌ Өшірулі"

    text = (
        f"{title}\n\n"                                 f"Қазіргі: {status}\n\n"
        f"_Жаңа күйді таңда:_"
    )                                          
    from keyboards import shuffle_toggle_kb
    await callback.message.edit_text(text, reply_markup=shuffle_toggle_kb("user", setting, current))                                                                                        
@router.callback_query(F.data.startswith("ushtoggle:"))                                       async def save_user_shuffle(callback: CallbackQuery):
    _, setting, value = callback.data.split(":")
    value = int(value)                             user_id = callback.from_user.id
                                                   if setting == "questions":
        await db.update_user_quiz_settings(user_id, shuffle_questions=value)                      elif setting == "answers":
        await db.update_user_quiz_settings(user_id, shuffle_answers=value)
                                                   await callback.answer("✅ Сақталды!", show_alert=True)
                                                   # Back to shuffle menu                         effective = await db.get_effective_quiz_settings(user_id)
                                                   sq_text = "✅ Қосулы" if effective['shuffle_questions'] else "❌ Өшірулі"                     sa_text = "✅ Қосулы" if effective['shuffle_answers'] else "❌ Өшірулі"
                                                   text = (                                           f"🎲 *Shuffle режимі* _(жаңартылды)_\n\n"
        f"🎲 Сұрақтар араластыру: {sq_text}\n"         f"🔀 Жауаптар араластыру: {sa_text}"       )

    from keyboards import shuffle_settings_kb      await callback.message.edit_text(text, reply_markup=shuffle_settings_kb("user"))
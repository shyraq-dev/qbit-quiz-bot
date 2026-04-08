from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove                         from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup                                              
from keyboards import main_menu_kb, feedback_type_kb
from notifications import notify_feedback      
router = Router()                              

class FeedbackState(StatesGroup):                  choosing_type = State()
    entering_text = State()                                                                                                                  @router.message(F.text == "💬 Кері байланыс")  async def feedback_menu(message: Message, state: FSMContext):                                     await state.clear()                            await state.set_state(FeedbackState.choosing_type)                                                                                           await message.answer(
        "💬 *Кері байланыс*\n\n"
        "Қандай түрде хабарласқыңыз келеді?",          reply_markup=feedback_type_kb()            )                                          
                                               @router.callback_query(FeedbackState.choosing_type, F.data.startswith("feedback:"))           async def feedback_type_chosen(callback, state: FSMContext):
    feedback_type = callback.data.split(":")[1]  # suggestion, complaint, bug, contact        
    await state.update_data(feedback_type=feedback_type)
    await state.set_state(FeedbackState.entering_text)
                                                   if feedback_type == "suggestion":                  text = (
            "💡 *Ұсыныс жіберу*\n\n"
            "Ботты жақсарту үшін ұсынысыңызды жазыңыз:\n\n"                                               "Болдырмау үшін /cancel"
        )                                          elif feedback_type == "complaint":
        text = (                                           "📋 *Шағым жіберу*\n\n"
            "Мәселені толық сипаттап жазыңыз:\n\n"                                                        "Болдырмау үшін /cancel"
        )
    elif feedback_type == "bug":                       text = (
            "🐛 *Қате туралы хабарлау*\n\n"                "Қатені сипаттаңыз:\n"                         "• Не болды?\n"                                "• Қалай қайталауға болады?\n"                 "• Скриншот бар ма?\n\n"
            "Болдырмау үшін /cancel"                   )                                          else:  # contact                                   text = (                                           "📞 *Әкімшімен байланысу*\n\n"
            "Хабарыңызды жазыңыз:\n\n"
            "Болдырмау үшін /cancel"
        )
                                                   await callback.message.edit_text(text)                                                                                                   @router.message(FeedbackState.entering_text, F.text == "/cancel")                             async def feedback_cancel(message: Message, state: FSMContext):
    await state.clear()                            await message.answer("❌ Болдырылмады.", reply_markup=main_menu_kb())                     
                                               @router.message(FeedbackState.entering_text)   async def feedback_submit(message: Message, state: FSMContext):                                   data = await state.get_data()
    feedback_type = data.get("feedback_type", "contact")
    feedback_text = message.text                                                                  user = message.from_user                                                                      # Notify admins via old system
    try:
        await notify_feedback(                             bot=message.bot,                               user_id=user.id,                               username=user.username or "",
            full_name=user.full_name or "Белгісіз",                                                       feedback_text=feedback_text,
            feedback_type=feedback_type                )
    except Exception:                                  pass

    await state.clear()                                                                           if feedback_type == "suggestion":                  response = (
            "✅ *Ұсынысыңыз жіберілді!*\n\n"
            "Админ қарастырып, жауап береді.\n"            "Рахмет! 🙏"
        )
    elif feedback_type == "complaint":                 response = (
            "✅ *Шағымыңыз жіберілді!*\n\n"                "Мәселені тексеріп, жақын арада шешеміз.\n"                                                   "Рахмет! 🙏"                               )
    elif feedback_type == "bug":                       response = (                                       "✅ *Қате туралы хабар жіберілді!*\n\n"
            "Қатені тексеріп, түзетеміз.\n"
            "Рахмет көмегіңіз үшін! 🙏"                )                                          else:  # contact                                   response = (
            "✅ *Хабарыңыз жіберілді!*\n\n"                "Админ жақын арада жауап береді.\n"            "Рахмет! 🙏"
        )                                      
    await message.answer(response, reply_markup=main_menu_kb())
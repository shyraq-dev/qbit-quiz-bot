from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, PollAnswer                                  from aiogram.fsm.context import FSMContext     from aiogram.fsm.state import State, StatesGroup                                              
import database as db
from keyboards import main_menu_kb             
router = Router()                                                                                                                            class QuizState(StatesGroup):                      in_quiz = State()                                                                         
# ═══ START QUIZ ═══                           
@router.message(F.text == "🎮 Quiz бастау")
async def start_quiz(message: Message, state: FSMContext):                                        # Get user settings
    user_id = message.from_user.id
    settings = await db.get_user_quiz_settings(user_id)

    if not settings:                                   bot_settings = await db.get_bot_settings()                                                    settings = {                                       'questions_count': bot_settings.get('default_questions_count', 15),                           'time_limit': bot_settings.get('default_time_limit', 30)                                  }                                      
    # Get random questions
    questions = await db.get_random_questions(settings['questions_count'])

    if not questions:                                  await message.answer(                              "❌ Сұрақтар жоқ!\n\n"                         "Админ сұрақ қосқанша күтіңіз.",
            reply_markup=main_menu_kb()                )                                              return
                                                   # Initialize quiz state
    await state.set_state(QuizState.in_quiz)
    await state.update_data(
        questions=[dict(q) for q in questions],        current_idx=0,                                 score=0,
        correct_count=0,                               wrong_count=0,                                 streak=0,
        max_streak=0,
        user_id=user_id,
        chat_id=message.chat.id
    )
                                                   await message.answer(
        f"🎮 *Quiz басталды!*\n\n"                     f"📊 Сұрақтар: {len(questions)}\n"
        f"⏱ Уақыт: {settings['time_limit']} сек\n\n"                                                  f"Бірінші сұрақ келеді...",
        reply_markup=main_menu_kb()
    )

    # Send first question                          await send_poll_question(message.bot, message.chat.id, state)                             
                                               async def send_poll_question(bot: Bot, chat_id: int, state: FSMContext):                          """Send question as Telegram Poll."""
    data = await state.get_data()                  questions = data['questions']
    idx = data['current_idx']                  
    if idx >= len(questions):
        # Quiz finished
        await show_results(bot, chat_id, state)
        return
                                                   q = questions[idx]                         
    # Prepare options                              options = [                                        q['option_a'],
        q['option_b'],                                 q['option_c'],
        q['option_d']                              ]

    if q.get('option_e'):                              options.append(q['option_e'])
    if q.get('option_f'):                              options.append(q['option_f'])                                                             # Get correct answer index (A=0, B=1, C=2, D=3, E=4, F=5)                                     correct_letter = q['correct'].upper()
    correct_idx = ord(correct_letter) - ord('A')                                              
    # Streak bar
    streak_bar = f" 🔥 {data['streak']}" if data['streak'] >= 2 else ""
                                                   # Question text with header
    question_text = (                                  f"📌 Сұрақ {idx + 1}/{len(questions)} | ⭐ {data['score']} ұпай{streak_bar}\n\n"              f"{q['question']}"                         )
                                                   # Send context if exists                       if q.get('context_text'):
        await bot.send_message(
            chat_id=chat_id,
            text=f"💬 *Мәнмәтін:*\n_{q['context_text']}_",                                                parse_mode="Markdown"
        )                                                                                         # Send image if exists
    if q.get('image_url'):
        from aiogram.types import URLInputFile         try:                                               photo = URLInputFile(q['image_url'])                                                          await bot.send_photo(chat_id=chat_id, photo=photo)                                        except:                                            pass                               
    # Send poll                                    poll_message = await bot.send_poll(                chat_id=chat_id,                               question=question_text,
        options=options,
        type="quiz",
        correct_option_id=correct_idx,                 is_anonymous=False,                            explanation=f"_{q['category']}_",              open_period=30
    )

    # Store poll ID
    await state.update_data(                           current_poll_id=poll_message.poll.id
    )                                          
                                               @router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer, state: FSMContext):
    """Handle poll answer from user."""
    current_state = await state.get_state()                                                       if current_state != QuizState.in_quiz:
        return                                                                                    data = await state.get_data()              
    # Check if correct user                        if poll_answer.user.id != data.get('user_id'):
        return                                 
    # Check if this is the current poll
    if poll_answer.poll_id != data.get('current_poll_id'):
        return                                 
    # Get question data
    idx = data['current_idx']                      questions = data['questions']                  q = questions[idx]

    # Get user's answer                            user_answer_idx = poll_answer.option_ids[0]

    # Get correct answer                           correct_letter = q['correct'].upper()
    correct_idx = ord(correct_letter) - ord('A')
                                                   is_correct = (user_answer_idx == correct_idx)                                             
    # Update score and streak
    if is_correct:                                     points = 1
        if data['streak'] >= 2:
            points = 2  # Bonus for streak

        new_score = data['score'] + points             new_streak = data['streak'] + 1                new_max_streak = max(data['max_streak'], new_streak)                                          new_correct = data['correct_count'] + 1
        new_wrong = data['wrong_count']
                                                       await state.update_data(
            score=new_score,                               streak=new_streak,
            max_streak=new_max_streak,                     correct_count=new_correct
        )                                                                                             # Send positive feedback
        accuracy = round(new_correct / (idx + 1) * 100, 1)                                            await poll_answer.bot.send_message(
            chat_id=data['chat_id'],                       text=(
                f"✅ Well done.\n\n"
                f"Accuracy: {accuracy}% · {new_correct} correct {new_wrong} wrong\n\n"                        f"Next — 🟢 Easy"
            )
        )                                      
    else:
        new_wrong = data['wrong_count'] + 1
        new_correct = data['correct_count']
                                                       await state.update_data(
            streak=0,  # Reset streak                      wrong_count=new_wrong
        )                                      
        # Send negative feedback                       accuracy = round(new_correct / (idx + 1) * 100, 1)                                            await poll_answer.bot.send_message(                chat_id=data['chat_id'],
            text=(
                f"❌ That's not right.\n"                      f"Streak reset.\n\n"
                f"Accuracy: {accuracy}% · {new_correct} correct {new_wrong} wrong\n\n"
                f"Next — 🟢 Easy"
            )                                          )
                                                   # Wait 1 second then send next                 import asyncio                                 await asyncio.sleep(1)                                                                        # Update index                                 new_idx = idx + 1                              await state.update_data(current_idx=new_idx)                                              
    # Send next question
    await send_poll_question(poll_answer.bot, data['chat_id'], state)
                                               
async def show_results(bot: Bot, chat_id: int, state: FSMContext):                                """Show final quiz results."""
    data = await state.get_data()              
    total = len(data['questions'])
    correct = data['correct_count']                wrong = data['wrong_count']
    score = data['score']                          accuracy = round(correct / total * 100, 1) if total > 0 else 0                            
    # Save to database
    user_id = data['user_id']                      await db.save_game_session(                        user_id=user_id,                               score=score,                                   total_questions=total,
        correct_answers=correct,                       streak=data['max_streak']                  )                                                                                             # Update user stats                            await db.update_user_score(user_id, score) 
    # Result text                                  result_text = (
        f"🏁 *Quiz аяқталды!*\n\n"                     f"📊 *Нәтижелер:*\n"
        f"   • Жалпы ұпай: *{score}*\n"                f"   • Дұрыс: {correct}/{total}\n"
        f"   • Қате: {wrong}/{total}\n"                f"   • Дәлдік: {accuracy}%\n"
        f"   • Max Streak: 🔥 {data['max_streak']}\n\n"
        f"Рахмет! 🎉"
    )                                                                                             await state.clear()
    await bot.send_message(                            chat_id=chat_id,
        text=result_text,                              reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )                                          

# ═══ CATEGORY/VARIANT QUIZ ═══
                                               @router.callback_query(F.data.startswith("start_variant:"))
async def start_variant_quiz(callback: CallbackQuery, state: FSMContext):
    """Start quiz from category variant."""        variant_id = int(callback.data.split(":")[1])                                                                                                # Get questions for this variant
    questions = await db.get_questions_by_variant(variant_id)

    if not questions:                                  await callback.answer("❌ Сұрақтар жоқ!", show_alert=True)
        return

    # Initialize quiz                              await state.set_state(QuizState.in_quiz)
    await state.update_data(                           questions=[dict(q) for q in questions],
        current_idx=0,                                 score=0,
        correct_count=0,                               wrong_count=0,                                 streak=0,                                      max_streak=0,
        user_id=callback.from_user.id,                 chat_id=callback.message.chat.id           )
                                                   await callback.message.answer(                     f"🎮 *Quiz басталды!*\n\n"                     f"📊 Сұрақтар: {len(questions)}\n\n"
        f"Бірінші сұрақ..."                        )
                                                   await send_poll_question(callback.bot, callback.message.chat.id, state)
    await callback.answer()
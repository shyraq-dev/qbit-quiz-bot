from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

import database as db
from keyboards import main_menu_kb

router = Router()


@router.message(F.text == "📊 Статистика")
@router.message(Command("stats"))
async def show_stats(message: Message):
    user = message.from_user
    stats = await db.get_user_stats(user.id)

    if not stats or stats["games_played"] == 0:
        await message.answer(
            "📊 Сенің статистикаң жоқ әлі.\n"
            "🎯 Алдымен тест тапсыр!",
            reply_markup=main_menu_kb(),
        )
        return

    total_answers = stats["correct_answers"] + stats["wrong_answers"]
    accuracy = round(stats["correct_answers"] / total_answers * 100) if total_answers else 0
    rank = await db.get_user_rank(user.id)

    # Progress bar (10 chars)
    filled = round(accuracy / 10)
    bar = "█" * filled + "░" * (10 - filled)

    text = (
        f"📊 *{user.first_name}-тің статистикасы*\n\n"
        f"🏅 Рейтингтегі орны: *#{rank}*\n\n"
        f"🎮 Ойындар: *{stats['games_played']}*\n"
        f"⭐ Жалпы ұпай: *{stats['total_score']}*\n\n"
        f"✅ Дұрыс жауаптар: *{stats['correct_answers']}*\n"
        f"❌ Қате жауаптар: *{stats['wrong_answers']}*\n"
        f"🎯 Дәлдік: *{accuracy}%*\n"
        f"`{bar}`\n\n"
        f"🔥 Ең үздік streak: *{stats['best_streak']}*\n"
        f"⚡ Қазіргі streak: *{stats['current_streak']}*"
    )

    await message.answer(text, reply_markup=main_menu_kb())
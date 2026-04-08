from aiogram import Router, F
from aiogram.types import Message              from aiogram.filters import Command            
import database as db
from keyboards import main_menu_kb
                                               router = Router()

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}           
                                               @router.message(F.text == "🏆 Рейтинг")        @router.message(Command("top"))                async def show_leaderboard(message: Message):      leaders = await db.get_leaderboard(limit=10)

    if not leaders:                                    await message.answer(
            "🏆 Рейтинг бос әлі.\n"
            "Бірінші болып тест тапсыр!",                  reply_markup=main_menu_kb(),
        )
        return
                                                   lines = ["🏆 *ТОП-10 Ойыншылар*\n"]
    for i, user in enumerate(leaders, 1):              medal = MEDALS.get(i, f"{i}.")                 name = user["full_name"] or user["username"] or "Белгісіз"                                    # Truncate long names
        if len(name) > 18:
            name = name[:16] + "…"                     lines.append(
            f"{medal} *{name}*\n"
            f"    ⭐ {user['total_score']} | 🎯 {user['accuracy']}% | 🔥 {user['best_streak']}"                                                      )
                                                   # Show current user's rank
    rank = await db.get_user_rank(message.from_user.id)
    my_stats = await db.get_user_stats(message.from_user.id)
                                                   if my_stats and my_stats["games_played"] > 0:                                                     lines.append(f"\n📍 *Сенің орның: #{rank}*  ⭐ {my_stats['total_score']}")
                                                   await message.answer(
        "\n".join(lines),                              reply_markup=main_menu_kb(),
    )
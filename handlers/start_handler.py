from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from database import get_or_create_user
from keyboards import main_menu_kb

router = Router()

ABOUT_TEXT = """
⚡ *QBit Quiz* — қазақша интеллект ойыны

📌 *Қалай жұмыс істейді?*
• Категория таңдайсың
• 10 сұраққа жауап бересің
• Ұпай жинайсың, рейтингке кіресің

🔥 *Streak жүйесі*
3 дұрыс қатарынан = бонус ұпай!

📤 *Сұрақ жіберу*
Өз сұрақтарыңды жіберіп, бот базасын толтыра аласың.

🏆 *Рейтинг*
Үздік ойыншылар кестесінде орын ал.

_Жылдам ойла. Дәл тап._
"""


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user

    # Check if user is new
    existing = await get_or_create_user(
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name or "Белгісіз",
    )

    # Notify admins if new user (games_played will be 0)
    if existing.get("games_played", 0) == 0:
        from notifications import notify_new_user
        try:
            await notify_new_user(
                bot=message.bot,
                user_id=user.id,
                username=user.username or "",
                full_name=user.full_name or "Белгісіз",
                language_code=user.language_code or ""
            )
        except Exception:
            pass  # Don't fail if notification fails

    await message.answer(
        f"👋 Сәлем, *{user.first_name}*!\n\n"
        "⚡ *QBit Quiz* қош келдің!\n"
        "_Білімді битке бөліп, жеңіске жина._\n\n"
        "Төмендегі мәзірден бастай аласың 👇",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Туралы")
async def cmd_about(message: Message):
    await message.answer(ABOUT_TEXT)
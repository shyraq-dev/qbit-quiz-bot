"""
Push notification system for admins
Sends automatic notifications to admins about important events
"""
from aiogram import Bot
from datetime import datetime
from config import ADMIN_IDS
import logging

logger = logging.getLogger(__name__)


async def notify_admins(bot: Bot, message: str, parse_mode: str = "Markdown"):
    """Send notification to all admins."""
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, message, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")


async def notify_new_user(bot: Bot, user_id: int, username: str,
                         full_name: str, language_code: str):
    """Notify admins about new user registration."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message = (
        f"🔔 *Жаңа қолданушы!*\n\n"
        f"👤 Аты: {full_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"🏷 Ник: @{username if username else 'жоқ'}\n"
        f"🌐 Тіл: {language_code or 'белгісіз'}\n"
        f"🕒 Уақыты: {timestamp}"
    )

    await notify_admins(bot, message)


async def notify_user_blocked(bot: Bot, user_id: int, username: str,
                              full_name: str):
    """Notify admins when user blocks the bot."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message = (
        f"🚫 *Қолданушы ботты бұғаттады*\n\n"
        f"👤 Аты: {full_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"🏷 Ник: @{username if username else 'жоқ'}\n"
        f"🕒 Уақыты: {timestamp}"
    )

    await notify_admins(bot, message)


async def notify_suggestion(bot: Bot, user_id: int, username: str,
                           full_name: str, suggestion_text: str):
    """Notify admins about new suggestion."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Truncate long suggestions
    if len(suggestion_text) > 200:
        suggestion_text = suggestion_text[:197] + "..."

    message = (
        f"🆕 *Жаңа ұсыныс түсті!*\n\n"
        f"👤 Қолданушы: {full_name} (@{username if username else 'жоқ'})\n"
        f"🆔 ID: `{user_id}`\n"
        f"📌 Ұсыныс:\n_{suggestion_text}_\n\n"
        f"🕒 Уақыты: {timestamp}\n\n"
        f"_Ұнаса, қабылдап ❤️ бас!_"
    )

    await notify_admins(bot, message)


async def notify_complaint(bot: Bot, user_id: int, username: str,
                          full_name: str, complaint_text: str):
    """Notify admins about new complaint."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if len(complaint_text) > 200:
        complaint_text = complaint_text[:197] + "..."

    message = (
        f"📋 *Жаңа шағым түсті!*\n\n"
        f"👤 Қолданушы: {full_name} (@{username if username else 'жоқ'})\n"
        f"🆔 ID: `{user_id}`\n"
        f"📌 Шағым:\n_{complaint_text}_\n\n"
        f"🕒 Уақыты: {timestamp}"
    )

    await notify_admins(bot, message)


async def notify_feedback(bot: Bot, user_id: int, username: str,
                         full_name: str, feedback_text: str,
                         feedback_type: str = "feedback"):
    """Notify admins about general feedback."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if len(feedback_text) > 200:
        feedback_text = feedback_text[:197] + "..."

    emoji = "💬" if feedback_type == "feedback" else "💡"
    title = "Кері байланыс" if feedback_type == "feedback" else "Ұсыныс"

    message = (
        f"{emoji} *Жаңа {title}!*\n\n"
        f"👤 Қолданушы: {full_name} (@{username if username else 'жоқ'})\n"
        f"🆔 ID: `{user_id}`\n"
        f"📌 Хабар:\n_{feedback_text}_\n\n"
        f"🕒 Уақыты: {timestamp}"
    )

    await notify_admins(bot, message)
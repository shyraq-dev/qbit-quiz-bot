import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers import (
    start_handler,
    quiz_handler,
    admin_handler,
    stats_handler,
    leaderboard_handler,
    settings_handler,
    category_variant_handler,
    ubt_handler,
    ubt_admin_handler,
    feedback_handler,
    broadcast_handler,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    # aiogram 3.7+ талабы: parse_mode DefaultBotProperties арқылы беріледі
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    # aiogram 3.25: Dispatcher storage параметрін тікелей қабылдайды
    dp = Dispatcher()

    # Register routers
    dp.include_router(start_handler.router)
    dp.include_router(ubt_handler.router)
    dp.include_router(ubt_admin_handler.router)
    dp.include_router(feedback_handler.router)
    dp.include_router(broadcast_handler.router)
    dp.include_router(settings_handler.router)
    dp.include_router(category_variant_handler.router)
    dp.include_router(quiz_handler.router)
    dp.include_router(admin_handler.router)
    dp.include_router(stats_handler.router)
    dp.include_router(leaderboard_handler.router)

    # Init DB before polling
    await init_db()

    logger.info("⚡ QBit Quiz Bot іске қосылды!")

    # Error handler for bot blocked detection
    # Error handler removed - was causing issues

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

"""Main entry point for the DungeonsBot."""

import asyncio
import logging

from bot.loader import bot, dp
from bot.handlers.all_handlers import router
from bot.database import init_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Start the bot with polling."""
    init_database()
    logger.info("Database initialized")

    dp.include_router(router)
    logger.info("Handlers included")

    logger.info("Bot started polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
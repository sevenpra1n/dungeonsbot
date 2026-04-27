"""Main entry point for the DungeonsBot."""

import asyncio
import logging

from bot.loader import bot, dp
from bot.handlers.all_handlers import router, _give_activity_rewards
from bot.handlers.start import router as start_router
from bot.handlers.profile import router as profile_router
from bot.database import init_database, get_all_completed_activities

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def activity_notification_loop():
    """Background task: check for completed activities every 2 seconds and notify players."""
    while True:
        await asyncio.sleep(2)
        try:
            completed = get_all_completed_activities()
            for activity in completed:
                user_id = activity['user_id']
                try:
                    await _give_activity_rewards(user_id, activity)
                except Exception as e:
                    logger.warning(f"Error giving activity rewards to {user_id}: {e}")
        except Exception as e:
            logger.warning(f"Activity loop error: {e}")


async def main():
    """Start the bot with polling."""
    init_database()
    logger.info("Database initialized")

    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(router)
    logger.info("Handlers included")

    logger.info("Bot started polling...")
    asyncio.create_task(activity_notification_loop())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
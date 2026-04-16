import logging
from aiogram import Bot, Dispatcher
from bot.all_handlers import router

# Configure logging
logging.basicConfig(level=logging.INFO)

API_TOKEN = 'YOUR_API_TOKEN'

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dispatcher = Dispatcher(bot)

# Include all handlers
dispatcher.include_router(router)

# Start polling
if __name__ == '__main__':
    import asyncio
    asyncio.run(dispatcher.start_polling())
"""Bot and Dispatcher instances. Import bot/dp from here."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import TOKEN, PROXY_URL

_session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else None
_default = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TOKEN, session=_session, default=_default) if _session else Bot(token=TOKEN, default=_default)
dp = Dispatcher(storage=MemoryStorage())

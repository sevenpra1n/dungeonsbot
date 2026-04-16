import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Ваш токен от BotFather
TOKEN = "Ваш токен"

# Прокси (опционально). Установите URL прокси для подключения без VPN,
# например: "socks5://user:pass@host:port" или "http://user:pass@host:port".
# Оставьте None чтобы не использовать прокси.
PROXY_URL = None

# ID администраторов (Telegram user_id). Добавьте нужные ID в список для доступа к /67
ADMIN_IDS = [0]

# ID игрока, который получает статус "багоюзер 777" (замените на нужный Telegram user_id)
BAGOUSER_ID = 0

# Настройка логирования
logging.basicConfig(level=logging.INFO)

_session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else None
_default = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TOKEN, session=_session, default=_default) if _session else Bot(token=TOKEN, default=_default)
dp = Dispatcher(storage=MemoryStorage())

# Имя файла базы данных
DB_NAME = "game_players.db"

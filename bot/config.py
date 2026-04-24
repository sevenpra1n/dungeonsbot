"""Bot configuration: token, proxy, admin IDs, DB name, and bot/dispatcher instances."""

import logging
import os

# Токен от BotFather. Задайте переменную окружения BOT_TOKEN перед запуском:
#   Windows:  set BOT_TOKEN=1234567890:AAFxxx...
#   Linux/Mac: export BOT_TOKEN=1234567890:AAFxxx...
TOKEN = os.environ.get("BOT_TOKEN", "")
if not TOKEN:
    raise ValueError(
        "Токен бота не задан! Установите переменную окружения BOT_TOKEN.\n"
        "Пример: set BOT_TOKEN=1234567890:AAFxxx..."
    )

# Прокси (опционально). Установите URL прокси для подключения без VPN,
# например: "socks5://user:pass@host:port" или "http://user:pass@host:port".
# Оставьте None чтобы не использовать прокси.
PROXY_URL = None

# ID администраторов (Telegram user_id). Добавьте нужные ID в список для доступа к /67
ADMIN_IDS = [0]

# ID игрока, который получает статус "багоюзер 777" (замените на нужный Telegram user_id)
BAGOUSER_ID = 0

# Имя файла базы данных
DB_NAME = "game_players.db"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

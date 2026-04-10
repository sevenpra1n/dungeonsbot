import asyncio
import logging
import os
import sqlite3
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

# ============== CUSTOM EMOJI CONSTANTS ==============
E_COINS    = '<tg-emoji emoji-id="5215420556089776398">👛</tg-emoji>'   # монеты
E_CRYSTALS = '<tg-emoji emoji-id="5429321386403327800">💎</tg-emoji>'   # кристаллы
E_TICKET   = '<tg-emoji emoji-id="5334675412599480338">📕</tg-emoji>'   # билет рейда
E_EXP      = '<tg-emoji emoji-id="5336829549151823064">📕</tg-emoji>'   # опыт
E_STAR     = '<tg-emoji emoji-id="5206476089127372379">⭐️</tg-emoji>'  # уровень/звезда
E_PROFILE  = '<tg-emoji emoji-id="5275979556308674886">👤</tg-emoji>'   # профиль
E_ONLINE   = '<tg-emoji emoji-id="5447410659077661506">🌐</tg-emoji>'   # онлайн режим
E_NICK     = '<tg-emoji emoji-id="5280968723463680459">🆔</tg-emoji>'   # никнейм
E_HP       = '<tg-emoji emoji-id="5267283746477861842">❤️</tg-emoji>'   # HP
E_DMG      = '<tg-emoji emoji-id="5429507440091612100">💥</tg-emoji>'   # урон
E_POW      = '<tg-emoji emoji-id="5242487302550199778">👊</tg-emoji>'   # мощь/сила
E_SWORD    = '<tg-emoji emoji-id="5393607290228067750">🗡</tg-emoji>'   # боевой меч / начало боя
E_CURSOR   = '<tg-emoji emoji-id="5438335517735267694">🖱</tg-emoji>'   # твой ход (начало)
E_MANA     = '<tg-emoji emoji-id="6280806319351927135">💜</tg-emoji>'   # мана
E_CROWN    = '<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji>'   # ты (PvP)
E_SKULL    = '<tg-emoji emoji-id="5274108672849491069">💀</tg-emoji>'   # враг (PvP)
E_ESWORD   = '<tg-emoji emoji-id="5438255528264348146">🗡</tg-emoji>'   # враг меч (PvP)
E_ANGRY    = '<tg-emoji emoji-id="5406708155956621268">😡</tg-emoji>'   # кик из клана

# Additional custom emoji
E_GIFT     = '<tg-emoji emoji-id="5429203678529613915">🎁</tg-emoji>'   # подарок/сила
E_TROPHY   = '<tg-emoji emoji-id="5312315739842026755">🏆</tg-emoji>'   # трофей/победы
E_BULLET   = '<tg-emoji emoji-id="5394892863081406649">▪️</tg-emoji>'   # маркер-пуля
E_INV_BOX  = '<tg-emoji emoji-id="5206702193385700709">📦</tg-emoji>'   # инвентарь
E_WOOD     = '<tg-emoji emoji-id="5449918202718985124">🌳</tg-emoji>'   # древесина
E_STONE    = '<tg-emoji emoji-id="5433955200849159326">🪨</tg-emoji>'   # камень
E_FOOD     = '<tg-emoji emoji-id="6284888960644682300">🥕</tg-emoji>'   # еда
E_IRON     = '<tg-emoji emoji-id="6280718212392816659">⛰</tg-emoji>'   # железо
E_GOLD_M   = '<tg-emoji emoji-id="6278282858561803026">🥇</tg-emoji>'   # золото (материал)
E_PLUS     = '<tg-emoji emoji-id="5397916757333654639">➕</tg-emoji>'   # плюс (награда)
E_CHECK    = '<tg-emoji emoji-id="5274559149922844956">✅</tg-emoji>'   # галочка
E_BELL     = '<tg-emoji emoji-id="5206222720416643915">🔔</tg-emoji>'   # колокол
E_TIMER    = '<tg-emoji emoji-id="5471952986970267163">🕑</tg-emoji>'   # таймер


# Ваш токен от BotFather
TOKEN = "Ваш токен"

# Прокси (опционально). Установите URL прокси для подключения без VPN,
# например: "socks5://user:pass@host:port" или "http://user:pass@host:port".
# Оставьте None чтобы не использовать прокси.
PROXY_URL = None

# ID администраторов (Telegram user_id). Добавьте нужные ID в список для доступа к /67
ADMIN_IDS = [0]

# Настройка логирования
logging.basicConfig(level=logging.INFO)

_session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else None
_default = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TOKEN, session=_session, default=_default) if _session else Bot(token=TOKEN, default=_default)
dp = Dispatcher(storage=MemoryStorage())

# ============== DATABASE SETUP ==============
DB_NAME = "game_players.db"

def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица игроков
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT NOT NULL,
            points REAL DEFAULT 0.0,
            click_power REAL DEFAULT 1.0,
            strength REAL DEFAULT 20.0,
            wins INTEGER DEFAULT 0,
            rating_points INTEGER DEFAULT 0,
            last_click TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Миграция: добавить столбцы если их нет
    for col_sql in [
        'ALTER TABLE players ADD COLUMN wins INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN rating_points INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN materials INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN raid_floor INTEGER DEFAULT 1',
        'ALTER TABLE players ADD COLUMN raid_max_floor INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN coins INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN crystals INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN raid_tickets INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN experience INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN player_level INTEGER DEFAULT 1',
        "ALTER TABLE players ADD COLUMN status TEXT DEFAULT 'Новичок'",
        'ALTER TABLE players ADD COLUMN online_matches INTEGER DEFAULT 0',
    ]:
        try:
            cursor.execute(col_sql)
            conn.commit()
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logging.warning(f"Migration warning: {e}")
    
    # Таблица покупок снаряжения
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipment_purchases (
            user_id INTEGER NOT NULL,
            equipment_id INTEGER NOT NULL,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, equipment_id),
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )
    ''')

    # Таблица текущего оружия игроков (кузня)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_weapons (
            user_id INTEGER PRIMARY KEY,
            weapon_id INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )
    ''')

    # Таблица текущей брони игроков (кузня)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_armor (
            user_id INTEGER PRIMARY KEY,
            armor_id INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )
    ''')

    # Миграция: добавить записи для существующих игроков, у которых ещё нет строк
    cursor.execute('''
        INSERT OR IGNORE INTO player_weapons (user_id, weapon_id)
        SELECT user_id, 0 FROM players
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO player_armor (user_id, armor_id)
        SELECT user_id, 0 FROM players
    ''')

    # Таблица кланов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clans (
            clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            clan_name TEXT NOT NULL UNIQUE,
            leader_id INTEGER NOT NULL,
            description TEXT,
            min_power INTEGER DEFAULT 0,
            clan_level INTEGER DEFAULT 1,
            clan_exp INTEGER DEFAULT 0,
            members_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (leader_id) REFERENCES players(user_id)
        )
    ''')

    # Таблица членов кланов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clan_members (
            user_id INTEGER NOT NULL,
            clan_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member' CHECK(role IN ('member', 'co_leader')),
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, clan_id),
            FOREIGN KEY (user_id) REFERENCES players(user_id),
            FOREIGN KEY (clan_id) REFERENCES clans(clan_id)
        )
    ''')
    # Миграция: добавить столбец role если отсутствует
    try:
        cursor.execute("ALTER TABLE clan_members ADD COLUMN role TEXT DEFAULT 'member'")
    except Exception:
        pass

    # Миграция: добавить столбец clan_image если отсутствует
    try:
        cursor.execute("ALTER TABLE clans ADD COLUMN clan_image TEXT DEFAULT NULL")
        conn.commit()
    except Exception:
        pass

    # Таблица статистики кланов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clan_stats (
            clan_id INTEGER PRIMARY KEY,
            total_wins INTEGER DEFAULT 0,
            total_enemies_defeated INTEGER DEFAULT 0,
            FOREIGN KEY (clan_id) REFERENCES clans(clan_id)
        )
    ''')

    # Таблица купленных скиллов игроков
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_skills (
            user_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, skill_id),
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )
    ''')

    # Таблица чата кланов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clan_chat (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            clan_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            nickname TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (clan_id) REFERENCES clans(clan_id),
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )
    ''')

    # Таблица инвентаря (материалы)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_inventory (
            user_id INTEGER PRIMARY KEY,
            food INTEGER DEFAULT 0,
            wood INTEGER DEFAULT 0,
            stone INTEGER DEFAULT 0,
            iron INTEGER DEFAULT 0,
            gold INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )
    ''')

    # Таблица активных активностей (локации)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_activities (
            user_id INTEGER PRIMARY KEY,
            activity_type TEXT,
            location_id INTEGER,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )
    ''')

    # Создать записи инвентаря для существующих игроков
    cursor.execute('''
        INSERT OR IGNORE INTO player_inventory (user_id)
        SELECT user_id FROM players
    ''')

    conn.commit()
    conn.close()

def add_player(user_id: int, nickname: str):
    """Добавить нового игрока в БД"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO players (user_id, nickname, points, click_power, strength, wins,
                                 materials, raid_floor, raid_max_floor,
                                 coins, crystals, raid_tickets, experience, player_level, status)
            VALUES (?, ?, 0.0, 1.0, 20.0, 0, 0, 1, 0, 100, 0, 0, 0, 1, 'Новичок')
        ''', (user_id, nickname))
        cursor.execute('''
            INSERT OR IGNORE INTO player_weapons (user_id, weapon_id) VALUES (?, 0)
        ''', (user_id,))
        cursor.execute('''
            INSERT OR IGNORE INTO player_armor (user_id, armor_id) VALUES (?, 0)
        ''', (user_id,))
        cursor.execute('''
            INSERT OR IGNORE INTO player_inventory (user_id) VALUES (?)
        ''', (user_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def get_player(user_id: int):
    """Получить данные игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, nickname, points, click_power, strength, wins, last_click, rating_points,
               COALESCE(materials, 0), COALESCE(raid_floor, 1), COALESCE(raid_max_floor, 0),
               COALESCE(coins, 0), COALESCE(crystals, 0), COALESCE(raid_tickets, 0),
               COALESCE(experience, 0), COALESCE(player_level, 1), COALESCE(status, 'Новичок'),
               COALESCE(online_matches, 0)
        FROM players
        WHERE user_id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "user_id": result[0],
            "nickname": result[1],
            "points": result[2],
            "click_power": result[3],
            "strength": result[4],
            "wins": result[5] if result[5] is not None else 0,
            "last_click": result[6],
            "rating_points": result[7] if result[7] is not None else 0,
            "materials": result[8],
            "raid_floor": result[9],
            "raid_max_floor": result[10],
            "coins": result[11],
            "crystals": result[12],
            "raid_tickets": result[13],
            "experience": result[14],
            "player_level": result[15],
            "status": result[16],
            "online_matches": result[17],
        }
    return None

def update_player_points(user_id: int, points: float):
    """Обновить очки игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE players 
        SET points = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (points, user_id))
    
    conn.commit()
    conn.close()

def update_player_strength(user_id: int, strength: float):
    """Обновить силу игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE players 
        SET strength = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (strength, user_id))
    
    conn.commit()
    conn.close()

def update_player_wins(user_id: int):
    """Увеличить счётчик побед на 1"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE players 
        SET wins = COALESCE(wins, 0) + 1, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()

def update_player_materials(user_id: int, materials: int):
    """Обновить количество материалов игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET materials = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (materials, user_id))
    conn.commit()
    conn.close()

def update_player_raid_floor(user_id: int, floor: int):
    """Обновить текущий этаж рейда игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET raid_floor = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (floor, user_id))
    conn.commit()
    conn.close()

def update_player_raid_max_floor(user_id: int, max_floor: int):
    """Обновить рекорд максимального этажа рейда"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET raid_max_floor = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (max_floor, user_id))
    conn.commit()
    conn.close()

def get_player_by_nickname(nickname: str):
    """Найти игрока по никнейму"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, nickname, points, click_power, strength FROM players WHERE nickname = ?
    ''', (nickname,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "user_id": result[0],
            "nickname": result[1],
            "points": result[2],
            "click_power": result[3],
            "strength": result[4],
        }
    return None

def add_points_to_player(user_id: int, amount: float):
    """Добавить очки игроку"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET points = points + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()

def add_strength_to_player(user_id: int, amount: float):
    """Добавить силу игроку"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET strength = strength + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()

def add_coins_to_player(user_id: int, amount: int):
    """Добавить монеты игроку"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET coins = COALESCE(coins, 0) + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()

def remove_coins_from_player(user_id: int, amount: int):
    """Снять монеты у игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET coins = MAX(0, COALESCE(coins, 0) - ?), updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()

def add_crystals_to_player(user_id: int, amount: int):
    """Добавить кристаллы игроку"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET crystals = COALESCE(crystals, 0) + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()

def add_raid_tickets_to_player(user_id: int, amount: int):
    """Добавить билеты рейда игроку"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET raid_tickets = COALESCE(raid_tickets, 0) + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()

def remove_raid_ticket(user_id: int):
    """Снять 1 билет рейда у игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET raid_tickets = MAX(0, COALESCE(raid_tickets, 0) - 1), updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

def add_online_match(user_id: int):
    """Добавить один онлайн-матч игроку"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET online_matches = COALESCE(online_matches, 0) + 1, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

# ============== EXPERIENCE SYSTEM ==============
EXPERIENCE_LEVELS = {
    1: 0, 2: 100, 3: 250, 4: 500, 5: 950,
    6: 1250, 7: 1800, 8: 2200, 9: 3000, 10: 4500,
    11: 7500, 12: 11500, 13: 14000, 14: 19000, 15: 25000,
    16: 32000, 17: 50000, 18: 80000, 19: 120000, 20: 200000,
}
MAX_PLAYER_LEVEL = 20

def _calc_level_from_exp(exp: int) -> int:
    """Рассчитать уровень по опыту"""
    level = 1
    for lvl in range(MAX_PLAYER_LEVEL, 0, -1):
        if exp >= EXPERIENCE_LEVELS[lvl]:
            level = lvl
            break
    return level

def add_experience_to_player(user_id: int, amount: int) -> dict:
    """Добавить опыт игроку, вернуть {'leveled_up': bool, 'new_level': int}"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COALESCE(experience, 0), COALESCE(player_level, 1) FROM players WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {'leveled_up': False, 'new_level': 1}
    old_exp, old_level = row
    new_exp = old_exp + amount
    new_level = _calc_level_from_exp(new_exp)
    cursor.execute('''
        UPDATE players SET experience = ?, player_level = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (new_exp, new_level, user_id))
    conn.commit()
    conn.close()
    return {'leveled_up': new_level > old_level, 'new_level': new_level}

def get_experience_progress(user_id: int) -> dict:
    """Вернуть {current_exp, needed_exp, level}"""
    player = get_player(user_id)
    if not player:
        return {'current_exp': 0, 'needed_exp': 100, 'level': 1}
    level = player['player_level']
    current_exp = player['experience']
    needed_exp = EXPERIENCE_LEVELS.get(level + 1, EXPERIENCE_LEVELS[MAX_PLAYER_LEVEL]) if level < MAX_PLAYER_LEVEL else current_exp
    return {'current_exp': current_exp, 'needed_exp': needed_exp, 'level': level}

# ============== STATUS SYSTEM ==============
STATUSES = {
    1: {"name": "Новичок",      "emoji": "🔸", "custom_emoji": '<tg-emoji emoji-id="5323718538710491847">🔸</tg-emoji>', "required_level": 1,  "type": "default"},
    2: {"name": "Продвинутый",  "emoji": "🌱", "custom_emoji": '<tg-emoji emoji-id="5343920308229256142">🌱</tg-emoji>', "required_level": 5,  "type": "unlock_level"},
    3: {"name": "Охотник",      "emoji": "🔪", "custom_emoji": '<tg-emoji emoji-id="5224460534534916102">🔪</tg-emoji>', "required_level": 1,  "type": "free"},
    4: {"name": "Любитель PVP", "emoji": "⚔️", "custom_emoji": '<tg-emoji emoji-id="5454014806950429357">⚔️</tg-emoji>', "required_level": 1,  "type": "free"},
    5: {"name": "Добытчик",     "emoji": "🥇", "custom_emoji": '<tg-emoji emoji-id="6278187557532472415">🥇</tg-emoji>', "required_level": 1,  "type": "free"},
}

def get_player_status_emoji(player: dict) -> str:
    """Вернуть кастомный HTML эмодзи статуса игрока"""
    status_name = player.get('status', 'Новичок')
    for s in STATUSES.values():
        if s['name'] == status_name:
            return s.get('custom_emoji', s['emoji'])
    return '<tg-emoji emoji-id="5323718538710491847">🔸</tg-emoji>'

def set_player_status(user_id: int, status_name: str):
    """Установить статус игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE players SET status = ? WHERE user_id = ?', (status_name, user_id))
    conn.commit()
    conn.close()

def get_available_statuses(user_id: int) -> dict:
    """Получить доступные статусы для игрока"""
    player = get_player(user_id)
    if not player:
        return {}
    available = {}
    for status_id, status_info in STATUSES.items():
        is_available = False
        if status_info["type"] in ("default", "free"):
            is_available = True
        elif status_info["type"] == "unlock_level":
            if player['player_level'] >= status_info.get('required_level', 1):
                is_available = True
        elif status_info["type"] == "unlock_matches":
            required = status_info.get('required_matches', 0) or 0
            if player.get('online_matches', 0) >= required:
                is_available = True
        if is_available:
            available[status_id] = status_info
    return available

# ============== INVENTORY FUNCTIONS ==============
def get_inventory(user_id: int) -> dict:
    """Получить инвентарь игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT food, wood, stone, iron, gold FROM player_inventory WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'food': row[0], 'wood': row[1], 'stone': row[2], 'iron': row[3], 'gold': row[4]}
    return {'food': 0, 'wood': 0, 'stone': 0, 'iron': 0, 'gold': 0}

def add_inventory_material(user_id: int, material: str, amount: int):
    """Добавить материал в инвентарь"""
    allowed = {'food', 'wood', 'stone', 'iron', 'gold'}
    if material not in allowed:
        return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO player_inventory (user_id) VALUES (?)', (user_id,))
    cursor.execute(f'UPDATE player_inventory SET {material} = COALESCE({material}, 0) + ? WHERE user_id = ?',
                   (amount, user_id))
    conn.commit()
    conn.close()

def add_all_inventory_materials(user_id: int, materials: dict):
    """Добавить сразу несколько материалов"""
    for mat, amt in materials.items():
        if amt > 0:
            add_inventory_material(user_id, mat, amt)

def add_admin_materials_to_player(user_id: int, amount: int):
    """Добавить все материалы игроку (для админ-панели)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO player_inventory (user_id) VALUES (?)', (user_id,))
    cursor.execute('''
        UPDATE player_inventory SET food = food + ?, wood = wood + ?, stone = stone + ?,
               iron = iron + ?, gold = gold + ? WHERE user_id = ?
    ''', (amount, amount, amount, amount, amount, user_id))
    conn.commit()
    conn.close()

# ============== ACTIVITY FUNCTIONS ==============
def start_activity(user_id: int, activity_type: str, location_id: int, duration_seconds: int):
    """Начать активность в локации"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.utcnow()
    end = datetime.utcnow().replace(microsecond=0)
    import datetime as dt
    end_time = now + dt.timedelta(seconds=duration_seconds)
    cursor.execute('''
        INSERT OR REPLACE INTO active_activities (user_id, activity_type, location_id, start_time, end_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, activity_type, location_id, now.isoformat(), end_time.isoformat()))
    conn.commit()
    conn.close()

def get_active_activity(user_id: int) -> dict | None:
    """Получить текущую активность игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT activity_type, location_id, start_time, end_time FROM active_activities WHERE user_id = ?',
                   (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'activity_type': row[0], 'location_id': row[1], 'start_time': row[2], 'end_time': row[3]}
    return None

def finish_activity(user_id: int):
    """Удалить запись активной активности"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM active_activities WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def check_activity_done(user_id: int) -> dict | None:
    """Проверить, завершилась ли активность. Вернуть данные если да, None если нет или нет активности."""
    activity = get_active_activity(user_id)
    if not activity:
        return None
    import datetime as dt
    try:
        end_time = datetime.fromisoformat(activity['end_time'])
    except Exception:
        return None
    now = datetime.utcnow()
    if now >= end_time:
        return activity
    return None

# ============== LOCATIONS ==============
LOCATIONS = {
    1: {
        "name": "🌾 Ясная Поляна",
        "emoji": "🌾",
        "image": "images/locations/meadow.png",
        "activities": {
            "gather": {
                "name": "Добыча еды",
                "time": 25,
                "emoji": "🌽",
                "rewards": {
                    "food": (2, 5),
                    "experience": (3, 8),
                    "coins": (10, 25)
                },
                "monster_chance": 0
            },
            "search": {
                "name": "Обыскать локацию",
                "time": 50,
                "emoji": "🗺️",
                "rewards": {
                    "coins": (20, 50),
                    "experience": (5, 15),
                    "food": (1, 3)
                },
                "monster_chance": 0.05
            }
        }
    }
}

# Враги в локациях: порог определяется силой игрока
LOCATION_ENEMIES = {
    "wolf": {
        "name": "Волк",
        "emoji": "🐺",
        "strength": 35,
        "min_player_strength": 0,
        "max_player_strength": 99,
    },
    "angry_hawk": {
        "name": "Яростный ястреб",
        "emoji": "🦅",
        "strength": 125,
        "min_player_strength": 100,
        "max_player_strength": 9999,
    },
}

def get_location_enemy_for_player(player_strength: float) -> dict:
    """Вернуть врага локации по силе игрока"""
    for enemy in LOCATION_ENEMIES.values():
        if enemy['min_player_strength'] <= player_strength <= enemy['max_player_strength']:
            return enemy
    # fallback
    return LOCATION_ENEMIES["wolf"]

def has_purchased_equipment(user_id: int, equipment_id: int) -> bool:
    """Проверить, купил ли игрок это снаряжение"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 1 FROM equipment_purchases
        WHERE user_id = ? AND equipment_id = ?
    ''', (user_id, equipment_id))
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

def add_equipment_purchase(user_id: int, equipment_id: int):
    """Добавить запись о покупке снаряжения"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO equipment_purchases (user_id, equipment_id)
        VALUES (?, ?)
    ''', (user_id, equipment_id))
    
    conn.commit()
    conn.close()

def get_player_weapon(user_id: int) -> int:
    """Получить текущий уровень оружия игрока (0 = стартовое)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT weapon_id FROM player_weapons WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def get_player_armor(user_id: int) -> int:
    """Получить текущий уровень брони игрока (0 = стартовая)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT armor_id FROM player_armor WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def set_player_weapon(user_id: int, weapon_id: int):
    """Установить оружие игрока и пересчитать силу"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO player_weapons (user_id, weapon_id) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET weapon_id = excluded.weapon_id
    ''', (user_id, weapon_id))
    conn.commit()
    conn.close()

def set_player_armor(user_id: int, armor_id: int):
    """Установить броню игрока и пересчитать силу"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO player_armor (user_id, armor_id) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET armor_id = excluded.armor_id
    ''', (user_id, armor_id))
    conn.commit()
    conn.close()

def get_leaderboard(limit: int = 10):
    """Получить рейтинг игроков (по силе)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT nickname, strength, COALESCE(wins, 0), COALESCE(rating_points, 0) FROM players
        WHERE strength > 0
        ORDER BY strength DESC
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

# ============== CLAN DB FUNCTIONS ==============
CLAN_LEVEL_EXP = {1: 100, 2: 250, 3: 500, 4: 950, 5: 1500}
MAX_CLAN_LEVEL = 5

# ============== SKILLS ==============
SKILLS = {
    1: {
        "name": "Мега-молот",
        "emoji": "✨",
        "desc": "Наносит 70% урона, шанс 35% заставить врага пропустить ход",
        "damage_mult": 0.7,
        "stun_chance": 0.35,
        "mana_cost": 30,
        "price": 1200,
    },
    2: {
        "name": "Кровавое неистовство",
        "emoji": "✨",
        "desc": "Наносит 2x урона, но вы теряете 15% от максимального HP",
        "damage_mult": 2.0,
        "hp_loss_pct": 0.15,
        "mana_cost": 50,
        "price": 2500,
    },
    3: {
        "name": "Ослепляющая вспышка",
        "emoji": "✨",
        "desc": "Снижает точность врага на 50% на 2 хода",
        "blind_turns": 2,
        "miss_chance_add": 0.5,
        "mana_cost": 100,
        "price": 7500,
    },
}

# ============== CLAN BUFFS ==============
CLAN_BUFFS = {
    1: {"power_pct": 0.0,  "click_bonus": 0},
    2: {"power_pct": 0.05, "click_bonus": 5},
    3: {"power_pct": 0.10, "click_bonus": 30},
    4: {"power_pct": 0.30, "click_bonus": 100},
    5: {"power_pct": 0.60, "click_bonus": 250},
}

CLAN_CHAT_MAX_MSG_LEN = 200  # Максимальная длина сообщения в чате клана

def update_rating_points(user_id: int, points: int):
    """Добавить очки рейтинга игроку"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players
        SET rating_points = COALESCE(rating_points, 0) + ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (points, user_id))
    conn.commit()
    conn.close()

def get_player_clan(user_id: int):
    """Получить клан игрока (None если нет клана)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.clan_id, c.clan_name, c.leader_id, c.description, c.min_power,
               c.clan_level, c.clan_exp, c.members_count, COALESCE(c.clan_image, NULL)
        FROM clans c
        JOIN clan_members cm ON c.clan_id = cm.clan_id
        WHERE cm.user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "clan_id": result[0],
            "clan_name": result[1],
            "leader_id": result[2],
            "description": result[3],
            "min_power": result[4],
            "clan_level": result[5],
            "clan_exp": result[6],
            "members_count": result[7],
            "clan_image": result[8],
        }
    return None

def get_clan(clan_id: int):
    """Получить клан по ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT clan_id, clan_name, leader_id, description, min_power,
               clan_level, clan_exp, members_count, COALESCE(clan_image, NULL)
        FROM clans WHERE clan_id = ?
    ''', (clan_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "clan_id": result[0],
            "clan_name": result[1],
            "leader_id": result[2],
            "description": result[3],
            "min_power": result[4],
            "clan_level": result[5],
            "clan_exp": result[6],
            "members_count": result[7],
            "clan_image": result[8],
        }
    return None

def create_clan(clan_name: str, leader_id: int, description: str) -> int:
    """Создать клан, вернуть clan_id (или -1 при ошибке)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO clans (clan_name, leader_id, description, members_count)
            VALUES (?, ?, ?, 1)
        ''', (clan_name, leader_id, description))
        clan_id = cursor.lastrowid
        cursor.execute('INSERT INTO clan_members (user_id, clan_id) VALUES (?, ?)', (leader_id, clan_id))
        cursor.execute('INSERT INTO clan_stats (clan_id) VALUES (?)', (clan_id,))
        conn.commit()
        return clan_id
    except sqlite3.IntegrityError:
        return -1
    finally:
        conn.close()

def join_clan(user_id: int, clan_id: int):
    """Вступить в клан"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO clan_members (user_id, clan_id) VALUES (?, ?)', (user_id, clan_id))
    cursor.execute('UPDATE clans SET members_count = members_count + 1 WHERE clan_id = ?', (clan_id,))
    conn.commit()
    conn.close()

def leave_clan(user_id: int, clan_id: int):
    """Выйти из клана"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM clan_members WHERE user_id = ? AND clan_id = ?', (user_id, clan_id))
    cursor.execute('UPDATE clans SET members_count = MAX(0, members_count - 1) WHERE clan_id = ?', (clan_id,))
    conn.commit()
    conn.close()

def kick_clan_member(user_id: int, clan_id: int):
    """Кикнуть члена из клана"""
    leave_clan(user_id, clan_id)

def delete_clan(clan_id: int):
    """Удалить клан и всех его членов"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM clan_members WHERE clan_id = ?', (clan_id,))
    cursor.execute('DELETE FROM clan_stats WHERE clan_id = ?', (clan_id,))
    cursor.execute('DELETE FROM clans WHERE clan_id = ?', (clan_id,))
    conn.commit()
    conn.close()

def set_clan_min_power(clan_id: int, min_power: int):
    """Установить минимальный порог входа"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE clans SET min_power = ? WHERE clan_id = ?', (min_power, clan_id))
    conn.commit()
    conn.close()

def add_clan_exp(clan_id: int, exp: int):
    """Добавить опыт клану, автоматически повышает уровень"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT clan_exp, clan_level FROM clans WHERE clan_id = ?', (clan_id,))
    result = cursor.fetchone()
    if result:
        new_exp = result[0] + exp
        level = result[1]
        while level < MAX_CLAN_LEVEL and new_exp >= CLAN_LEVEL_EXP[level]:
            level += 1
        cursor.execute('UPDATE clans SET clan_exp = ?, clan_level = ? WHERE clan_id = ?',
                       (new_exp, level, clan_id))
    conn.commit()
    conn.close()

def get_all_clans():
    """Получить список всех кланов"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.clan_id, c.clan_name, c.clan_level, c.members_count, c.min_power,
               p.nickname AS leader_name
        FROM clans c
        JOIN players p ON c.leader_id = p.user_id
        ORDER BY c.clan_level DESC, c.clan_exp DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    return results

def get_clan_members(clan_id: int):
    """Получить список членов клана (user_id, nickname, strength, role)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.user_id, p.nickname, p.strength, cm.role
        FROM players p
        JOIN clan_members cm ON p.user_id = cm.user_id
        WHERE cm.clan_id = ?
    ''', (clan_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_clan_member_role(user_id: int, clan_id: int) -> str:
    """Получить роль участника клана ('leader', 'co_leader', 'member')"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM clan_members WHERE user_id = ? AND clan_id = ?', (user_id, clan_id))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'member'

def set_clan_member_role(user_id: int, clan_id: int, role: str):
    """Установить роль участнику клана"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE clan_members SET role = ? WHERE user_id = ? AND clan_id = ?',
                   (role, user_id, clan_id))
    conn.commit()
    conn.close()

def get_clan_co_leaders(clan_id: int) -> list:
    """Получить список соруководителей клана"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.user_id, p.nickname
        FROM players p
        JOIN clan_members cm ON p.user_id = cm.user_id
        WHERE cm.clan_id = ? AND cm.role = 'co_leader'
    ''', (clan_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def update_clan_name(clan_id: int, new_name: str) -> bool:
    """Обновить название клана. Возвращает False если имя уже занято."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE clans SET clan_name = ? WHERE clan_id = ?', (new_name, clan_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_clan_description(clan_id: int, description: str):
    """Обновить описание клана"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE clans SET description = ? WHERE clan_id = ?', (description, clan_id))
    conn.commit()
    conn.close()

def update_clan_image(clan_id: int, image_file_id: str):
    """Обновить картину клана (Telegram file_id)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE clans SET clan_image = ? WHERE clan_id = ?', (image_file_id, clan_id))
    conn.commit()
    conn.close()

def save_clan_message(clan_id: int, user_id: int, nickname: str, message: str):
    """Сохранить сообщение в чат клана"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO clan_chat (clan_id, user_id, nickname, message) VALUES (?, ?, ?, ?)',
        (clan_id, user_id, nickname, message)
    )
    conn.commit()
    conn.close()

def get_clan_messages(clan_id: int, limit: int = 30) -> list:
    """Получить последние сообщения из чата клана"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT nickname, message, sent_at
        FROM clan_chat
        WHERE clan_id = ?
        ORDER BY message_id DESC
        LIMIT ?
    ''', (clan_id, limit))
    results = cursor.fetchall()
    conn.close()
    return list(reversed(results))

# ============== SKILLS DB FUNCTIONS ==============
def get_player_skills(user_id: int) -> list:
    """Получить список ID купленных скиллов игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT skill_id FROM player_skills WHERE user_id = ?', (user_id,))
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

def has_purchased_skill(user_id: int, skill_id: int) -> bool:
    """Проверить, куплен ли скилл"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM player_skills WHERE user_id = ? AND skill_id = ?', (user_id, skill_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_skill_purchase(user_id: int, skill_id: int):
    """Записать покупку скилла"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO player_skills (user_id, skill_id) VALUES (?, ?)', (user_id, skill_id))
    conn.commit()
    conn.close()

# ============== EQUIPMENT ==============
EQUIPMENT = {
    1: {"name": "деревянный меч", "strength": 15, "cost": 50, "emoji": "🗡️"},
    2: {"name": "железный меч", "strength": 30, "cost": 150, "emoji": "🗡️"},
    3: {"name": "золотой меч", "strength": 50, "cost": 350, "emoji": "🗡️"},
    4: {"name": "кожаная одежда", "strength": 60, "cost": 550, "emoji": "👕"},
    5: {"name": "гаечный ключ", "strength": 85, "cost": 850, "emoji": "🔧"}
}

# ============== FORGE: WEAPONS & ARMOR ==============
DEFAULT_WEAPON = {"name": "палка", "strength": 10, "emoji": "🔹"}
DEFAULT_ARMOR = {"name": "трусы", "strength": 10, "emoji": "🔹"}

WEAPONS = {
    1:  {"name": "большая палка",              "strength": 16,  "cost": 50,    "emoji": "🔹"},
    2:  {"name": "деревянный меч",             "strength": 22,  "cost": 110,   "emoji": "🔹"},
    3:  {"name": "каменная булава",            "strength": 31,  "cost": 200,   "emoji": "🔹"},
    4:  {"name": "золотой клинок",             "strength": 40,  "cost": 345,   "emoji": "🔹"},
    5:  {"name": "железный меч",               "strength": 55,  "cost": 650,   "emoji": "🔹"},
    6:  {"name": "зачарованный золотой меч",   "strength": 70,  "cost": 1150,  "emoji": "🔸"},
    7:  {"name": "алмазный клинок",            "strength": 95,  "cost": 1750,  "emoji": "🔸"},
    8:  {"name": "катана",                     "strength": 125, "cost": 2800,  "emoji": "🔸"},
    9:  {"name": "мурасама",                   "strength": 165, "cost": 4500,  "emoji": "🔸"},
    10: {"name": "огненный клинок",            "strength": 200, "cost": 10000, "emoji": "♦️"},
}

ARMOR = {
    1:  {"name": "кожаный торс и трусы",  "strength": 16,  "cost": 50,    "emoji": "🔹"},
    2:  {"name": "тканевая одежда",        "strength": 22,  "cost": 110,   "emoji": "🔹"},
    3:  {"name": "кожанные доспехи",       "strength": 31,  "cost": 200,   "emoji": "🔹"},
    4:  {"name": "кольчуга",               "strength": 40,  "cost": 345,   "emoji": "🔹"},
    5:  {"name": "железные доспехи",       "strength": 55,  "cost": 650,   "emoji": "🔹"},
    6:  {"name": "золотые доспехи",        "strength": 70,  "cost": 1150,  "emoji": "🔸"},
    7:  {"name": "стальные доспехи",       "strength": 95,  "cost": 1750,  "emoji": "🔸"},
    8:  {"name": "алмазные доспехи",       "strength": 125, "cost": 2800,  "emoji": "🔸"},
    9:  {"name": "обсидиановые доспехи",   "strength": 165, "cost": 4500,  "emoji": "🔸"},
    10: {"name": "легендарные доспехи",    "strength": 200, "cost": 10000, "emoji": "♦️"},
}

# ============== ENEMIES ==============
ENEMIES = {
    1: {"name": "Гоблин", "health": 50, "reward": 30, "base_damage": 8},
    2: {"name": "Лучник", "health": 120, "reward": 60, "base_damage": 15},
    3: {"name": "Дровосек", "health": 300, "reward": 90, "base_damage": 25},
    4: {"name": "Гоблин-гигант", "health": 640, "reward": 120, "base_damage": 40},
    5: {"name": "Дух леса", "health": 950, "reward": 190, "base_damage": 60}
}

# ============== RAID FLOORS ==============
RAID_FLOORS = {
    1:  {"name": "летучая мышь",      "health": 60,   "reward": 10,  "base_damage": 15,  "emoji": "💀"},
    2:  {"name": "крыса",             "health": 140,  "reward": 25,  "base_damage": 35,  "emoji": "💀"},
    3:  {"name": "слизень",           "health": 200,  "reward": 40,  "base_damage": 50,  "emoji": "💀"},
    4:  {"name": "большой слизень",   "health": 340,  "reward": 80,  "base_damage": 85,  "emoji": "💀"},
    5:  {"name": "скелет",            "health": 440,  "reward": 110, "base_damage": 110, "emoji": "💀"},
    6:  {"name": "гоблин",            "health": 600,  "reward": 145, "base_damage": 150, "emoji": "💀"},
    7:  {"name": "проклятый доспех",  "health": 740,  "reward": 210, "base_damage": 185, "emoji": "💀"},
    8:  {"name": "железная дева",     "health": 840,  "reward": 350, "base_damage": 210, "emoji": "💀"},
    9:  {"name": "призрачный палач",  "health": 1280, "reward": 520, "base_damage": 320, "emoji": "💀"},
    10: {"name": "зеркальный дух",    "health": 2000, "reward": 700, "base_damage": 500, "emoji": "♦️💀"},
}

# ============== STATES ==============
class Registration(StatesGroup):
    waiting_for_nickname = State()

class EquipmentMenu(StatesGroup):
    viewing_equipment = State()

class ForgeMenu(StatesGroup):
    viewing_forge = State()
    viewing_weapons = State()
    viewing_armor = State()
    viewing_skills = State()

class BattleState(StatesGroup):
    viewing_enemies = State()
    in_battle = State()
    enemy_attacking = State()
    battle_round = State()

class RaidState(StatesGroup):
    in_raid = State()

class OnlineState(StatesGroup):
    searching = State()
    waiting_accept = State()
    in_pvp_battle = State()

class ClanMenu(StatesGroup):
    viewing_clans = State()
    creating_clan_confirm = State()
    creating_clan_name = State()
    creating_clan_description = State()
    viewing_my_clan = State()
    kicking_member = State()
    changing_min_power = State()
    deleting_clan_confirm = State()
    promoting_member = State()
    demoting_member = State()
    in_clan_chat = State()
    selecting_clan_customization = State()
    changing_clan_name = State()
    changing_clan_description = State()
    changing_clan_image = State()

class AdminPanel(StatesGroup):
    main_menu = State()
    adding_coins_nickname = State()
    adding_coins_amount = State()
    adding_strength_nickname = State()
    adding_strength_amount = State()
    adding_experience_nickname = State()
    adding_experience_amount = State()
    adding_crystals_nickname = State()
    adding_crystals_amount = State()
    adding_raid_tickets_nickname = State()
    adding_raid_tickets_amount = State()
    adding_materials_nickname = State()
    adding_materials_amount = State()

class LocationMenu(StatesGroup):
    viewing_map = State()
    viewing_location = State()
    searching_enemy = State()

class ProfileMenu(StatesGroup):
    viewing_profile = State()
    viewing_statuses = State()
    viewing_inventory = State()

# Словарь для отслеживания cooldown боевых действий (2 сек)
battle_cooldowns: dict = {}

# Очередь поиска PvP: user_id -> {nickname, strength, wins, chat_id}
pvp_queue: dict = {}
# Активные PvP пары: user_id -> opponent_user_id
pvp_pairs: dict = {}

# Активные сессии клан-чата: clan_id -> set(user_id)
clan_chat_sessions: dict = {}

# ============== KEYBOARDS ==============
def get_main_kb():
    """Главное меню"""
    kb = [
        [KeyboardButton(text="🗺️ Карта"),      KeyboardButton(text="📦 Инвентарь")],
        [KeyboardButton(text="🔨 Кузня"),        KeyboardButton(text="⚔️ Враги")],
        [KeyboardButton(text="🐉 Рейд"),         KeyboardButton(text="🌐 Онлайн")],
        [KeyboardButton(text="🛡️ Кланы"),       KeyboardButton(text="🏆 Рейтинг")],
        [KeyboardButton(text="📖 Профиль")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_forge_kb():
    """Главное меню кузни"""
    kb = [
        [KeyboardButton(text="⚔️ Оружие"), KeyboardButton(text="🛡️ Броня")],
        [KeyboardButton(text="✨ Скиллы")],
        [KeyboardButton(text="❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_weapons_kb():
    """Меню выбора оружия"""
    kb = []
    for w_id, w_info in WEAPONS.items():
        btn = f"{w_info['emoji']} {w_info['name']} (сила: {w_info['strength']}) — {w_info['cost']} монет"
        kb.append([KeyboardButton(text=btn)])
    kb.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_armor_kb():
    """Меню выбора брони"""
    kb = []
    for a_id, a_info in ARMOR.items():
        btn = f"{a_info['emoji']} {a_info['name']} (сила: {a_info['strength']}) — {a_info['cost']} монет"
        kb.append([KeyboardButton(text=btn)])
    kb.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_equipment_kb():
    """Меню снаряжения (устарело, оставлено для совместимости)"""
    kb = []
    
    for equip_id, equip_info in EQUIPMENT.items():
        button_text = f"{equip_info['emoji']} {equip_info['name']} (+{equip_info['strength']}) - {equip_info['cost']} очков"
        kb.append([KeyboardButton(text=button_text)])
    
    kb.append([KeyboardButton(text="❌ Выход")])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_enemies_kb():
    """Меню врагов"""
    kb = []
    
    for enemy_id, enemy_info in ENEMIES.items():
        button_text = f"{enemy_info['name']} 🩶 {enemy_info['health']}"
        kb.append([KeyboardButton(text=button_text)])
    
    kb.append([KeyboardButton(text="❌ Вернуться")])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_battle_kb():
    """Меню боя"""
    kb = [
        [KeyboardButton(text="⚔️ Начать сражение")],
        [KeyboardButton(text="❌ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_battle_action_kb(user_id: int = None, mana: int = 100) -> ReplyKeyboardMarkup:
    """Меню действий в бою (динамическое: добавляет кнопки скиллов если куплены и хватает маны)"""
    kb = [
        [KeyboardButton(text="🗡️ Атаковать")],
        [KeyboardButton(text="Крит💥20%")]
    ]
    if user_id is not None:
        for skill_id, skill in SKILLS.items():
            if has_purchased_skill(user_id, skill_id) and mana >= skill['mana_cost']:
                kb.append([KeyboardButton(text=f"✨ Скилл {skill_id}: {skill['name']}")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_end_battle_kb():
    """Меню после боя"""
    kb = [
        [KeyboardButton(text="🏠 В главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_monster_encounter_kb() -> ReplyKeyboardMarkup:
    """Клавиатура встречи с монстром после активности"""
    kb = [
        [KeyboardButton(text="⚔️ Сразиться с монстром")],
        [KeyboardButton(text="🏃 Убежать")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_searching_kb():
    """Меню поиска соперника"""
    kb = [
        [KeyboardButton(text="🚫 Прекратить поиск")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_pvp_accept_kb():
    """Меню подтверждения PvP"""
    kb = [
        [KeyboardButton(text="✅ Принять игру")],
        [KeyboardButton(text="❌ Отклонить")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_next_weapon_kb(current_weapon_id: int) -> ReplyKeyboardMarkup:
    """Клавиатура для следующего уровня оружия"""
    next_id = current_weapon_id + 1
    if next_id > max(WEAPONS.keys()):
        kb = [
            [KeyboardButton(text="✅ Вы достигли максимума")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    else:
        w = WEAPONS[next_id]
        btn = f"{w['emoji']} {w['name']} (сила: {w['strength']}) — {w['cost']} монет"
        kb = [
            [KeyboardButton(text=btn)],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_next_armor_kb(current_armor_id: int) -> ReplyKeyboardMarkup:
    """Клавиатура для следующего уровня брони"""
    next_id = current_armor_id + 1
    if next_id > max(ARMOR.keys()):
        kb = [
            [KeyboardButton(text="✅ Вы достигли максимума")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    else:
        a = ARMOR[next_id]
        btn = f"{a['emoji']} {a['name']} (сила: {a['strength']}) — {a['cost']} монет"
        kb = [
            [KeyboardButton(text=btn)],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_skills_kb(user_id: int) -> ReplyKeyboardMarkup:
    """Меню скиллов в кузне"""
    kb = []
    for skill_id, skill in SKILLS.items():
        owned = has_purchased_skill(user_id, skill_id)
        status = "✅" if owned else f"{skill['price']} монет"
        kb.append([KeyboardButton(text=f"{skill['emoji']} {skill['name']} [{status}]")])
    kb.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_clans_list_kb(clans: list) -> ReplyKeyboardMarkup:
    """Клавиатура со списком кланов"""
    kb = []
    for clan in clans:
        clan_id, clan_name, clan_level, members_count, min_power, leader_name = clan
        btn = f"🛡️ {clan_name} [ур.{clan_level}] [{members_count}👥] [{min_power}⚔️]"
        kb.append([KeyboardButton(text=btn)])
    kb.append([KeyboardButton(text="➕ Создать клан")])
    kb.append([KeyboardButton(text="❌ Вернуться")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_create_clan_confirm_kb()-> ReplyKeyboardMarkup:
    """Подтверждение создания клана"""
    kb = [
        [KeyboardButton(text="✅ Да, создать")],
        [KeyboardButton(text="❌ Нет")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_my_clan_kb(is_leader: bool, is_co_leader: bool = False) -> ReplyKeyboardMarkup:
    """Меню своего клана"""
    kb = []
    if is_leader:
        kb.append([KeyboardButton(text="👢 Кикнуть игрока")])
        kb.append([KeyboardButton(text="⭐ Назначить соруководителя")])
        kb.append([KeyboardButton(text="⬇️ Снять соруководителя")])
        kb.append([KeyboardButton(text="⚙️ Изменить порог")])
        kb.append([KeyboardButton(text="🎨 Изменить оформление")])
        kb.append([KeyboardButton(text="🗑️ Удалить клан")])
    elif is_co_leader:
        kb.append([KeyboardButton(text="👢 Кикнуть игрока")])
        kb.append([KeyboardButton(text="🚪 Выйти из клана")])
    else:
        kb.append([KeyboardButton(text="🚪 Выйти из клана")])
    kb.append([KeyboardButton(text="💬 Чат клана")])
    kb.append([KeyboardButton(text="🔙 Вернуться")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_kick_members_kb(members: list, leader_id: int, co_leader_ids: list = None) -> ReplyKeyboardMarkup:
    """Клавиатура со списком членов для кика (нельзя кикнуть главу или других соруководителей для соруков)"""
    if co_leader_ids is None:
        co_leader_ids = []
    kb = []
    for member in members:
        uid, nickname = member[0], member[1]
        if uid != leader_id and uid not in co_leader_ids:
            kb.append([KeyboardButton(text=f"👤 {nickname}")])
    kb.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_promote_members_kb(members: list, leader_id: int) -> ReplyKeyboardMarkup:
    """Клавиатура для назначения соруководителя"""
    kb = []
    for member in members:
        uid, nickname, _strength, role = member
        if uid != leader_id and role != 'co_leader':
            kb.append([KeyboardButton(text=f"👤 {nickname}")])
    kb.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_demote_members_kb(co_leaders: list) -> ReplyKeyboardMarkup:
    """Клавиатура для снятия соруководителей"""
    kb = []
    for uid, nickname in co_leaders:
        kb.append([KeyboardButton(text=f"⭐ {nickname}")])
    kb.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_clan_chat_kb() -> ReplyKeyboardMarkup:
    """Клавиатура в чате клана"""
    kb = [[KeyboardButton(text="🚪 Выйти из чата")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_delete_clan_confirm_kb() -> ReplyKeyboardMarkup:
    """Подтверждение удаления клана"""
    kb = [
        [KeyboardButton(text="✅ Да, удалить")],
        [KeyboardButton(text="❌ Нет")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_admin_kb() -> ReplyKeyboardMarkup:
    """Клавиатура админ панели"""
    kb = [
        [KeyboardButton(text="💰 Накрутить монеты")],
        [KeyboardButton(text="💪 Накрутить силу")],
        [KeyboardButton(text="⭐️ Накрутить опыт")],
        [KeyboardButton(text="💎 Накрутить кристаллы")],
        [KeyboardButton(text="📕 Накрутить билеты рейда")],
        [KeyboardButton(text="🥕 Накрутить материалы")],
        [KeyboardButton(text="❌ Выход")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_map_kb() -> ReplyKeyboardMarkup:
    """Клавиатура карты"""
    kb = []
    for loc_id, loc in LOCATIONS.items():
        kb.append([KeyboardButton(text=loc['name'])])
    kb.append([KeyboardButton(text="❌ Вернуться")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_location_activities_kb(location_id: int) -> ReplyKeyboardMarkup:
    """Клавиатура активностей локации"""
    loc = LOCATIONS.get(location_id)
    if not loc:
        return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Вернуться")]], resize_keyboard=True)
    kb = []
    for act_key, act in loc['activities'].items():
        kb.append([KeyboardButton(text=f"{act['emoji']} {act['name']} ({act['time']}с)")])
    if location_id == 1:
        kb.append([KeyboardButton(text="🔍 Поиск врага (10с)")])
    kb.append([KeyboardButton(text="⬅️ Назад на карту")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_profile_kb() -> ReplyKeyboardMarkup:
    """Клавиатура профиля"""
    kb = [
        [KeyboardButton(text="🎭 Статусы"), KeyboardButton(text="📦 Инвентарь")],
        [KeyboardButton(text="🏠 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_statuses_kb(player: dict) -> ReplyKeyboardMarkup:
    """Клавиатура статусов"""
    kb = []
    for s_id, s in STATUSES.items():
        owned = (player.get('status') == s['name'])
        can_unlock = (player.get('player_level', 1) >= s.get('required_level', 1))
        if owned:
            label = f"{s['emoji']} {s['name']} [✅ Активен]"
        elif can_unlock:
            label = f"{s['emoji']} {s['name']} [Выбрать]"
        else:
            label = f"{s['emoji']} {s['name']} [🔒 Ур.{s.get('required_level', 1)}]"
        kb.append([KeyboardButton(text=label)])
    kb.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ============== HELPER FUNCTIONS ==============
def calculate_player_health(strength: float) -> int:
    """Рассчитать здоровье игрока (сила * 0.9)"""
    return int(round(strength * 0.9))

def calculate_damage(strength: float) -> int:
    """Рассчитать урон (сила * 0.3)"""
    return int(round(strength * 0.3))

def calculate_enemy_damage(enemy_id: int) -> int:
    """Рассчитать урон врага (здоровье врага * 0.4)"""
    enemy_health = ENEMIES[enemy_id]['health']
    return int(round(enemy_health * 0.4))

def can_battle_action(user_id: int) -> bool:
    """Проверить cooldown боевого действия (2 секунды)"""
    now = datetime.now()
    last = battle_cooldowns.get(user_id)
    if last and (now - last).total_seconds() < 2.0:
        return False
    battle_cooldowns[user_id] = now
    return True

def reset_battle_cooldown(user_id: int):
    """Сбросить cooldown боя (при переходе на новый этаж)"""
    battle_cooldowns.pop(user_id, None)

def apply_clan_strength_buff(strength: float, clan_level: int) -> float:
    """Применить бафф клана к силе игрока"""
    buff = CLAN_BUFFS.get(clan_level, CLAN_BUFFS[1])
    return strength * (1 + buff['power_pct'])

def get_clan_click_bonus(clan_level: int) -> float:
    """Получить бонус мощи клика от клана"""
    buff = CLAN_BUFFS.get(clan_level, CLAN_BUFFS[1])
    return buff['click_bonus']

def roll_miss(extra_miss_chance: float = 0.0) -> bool:
    """Вернуть True если атака промахивается (10% база + доп. шанс от ослепления)"""
    return random.random() < (0.10 + extra_miss_chance)


async def send_image_with_text(message, image_path: str, text: str, reply_markup=None):
    """Отправить изображение с текстом. Если файл не найден — отправить только текст."""
    try:
        if not os.path.exists(image_path):
            print(f"⚠️ ФАЙЛ НЕ НАЙДЕН: {image_path}")
            await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
            return
        photo = FSInputFile(image_path)
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


# ============== COMMANDS ==============
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if player:
        await message.answer("Ты уже зарегистрирован!", reply_markup=get_main_kb())
    else:
        await message.answer("Привет! Давай начнем. Как тебя будут звать в игре? Введи свой никнейм:")
        await state.set_state(Registration.waiting_for_nickname)

@dp.message(Registration.waiting_for_nickname)
async def process_nickname(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    nickname = message.text
    
    add_player(user_id, nickname)
    
    await state.clear()
    await message.answer(f"Приятно познакомиться, {nickname}! Теперь ты можешь приступать.", reply_markup=get_main_kb())

# ============== PROFILE ==============
@dp.message(Command("профиль"))
@dp.message(F.text == "/профиль")
@dp.message(F.text == "📖 Профиль")
async def show_profile(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Профиль не найден. Напиши /start")
        return

    await state.set_state(ProfileMenu.viewing_profile)
    await _send_profile(message, player)

async def _send_profile(message, player: dict):
    """Отправить сообщение профиля"""
    health = calculate_player_health(player['strength'])
    damage = calculate_damage(player['strength'])
    exp_info = get_experience_progress(player['user_id'])
    status_emoji = get_player_status_emoji(player)

    response = (
        f'{E_PROFILE} <b>Профиль игрока:</b>\n'
        f'🔒 {E_BULLET} {player["nickname"]}\n\n'
        f'{status_emoji} <b>{player["status"]}</b>\n\n'
        f'{E_EXP} Очки опыта {E_BULLET} {exp_info["current_exp"]} / {exp_info["needed_exp"]}\n'
        f'Уровень {E_BULLET} {player["player_level"]}{E_STAR}\n\n'
        f'│{E_TROPHY}│ {player["wins"]} {E_BULLET} Победы\n'
        f'│{E_GIFT}│ {int(player["strength"])} {E_BULLET} Сила\n'
        f'│{E_HP}│ {health} {E_BULLET} Здоровье\n\n'
        f'┆{E_COINS}┆ Монеты {E_BULLET} {player["coins"]}\n'
        f'┆{E_CRYSTALS}┆ Кристаллы {E_BULLET} {player["crystals"]}\n'
        f'┆{E_TICKET}┆ Билеты рейда {E_BULLET} {player["raid_tickets"]}\n'
    )
    await send_image_with_text(message, "images/profiles/profile_default.png", response, reply_markup=get_profile_kb())

@dp.message(ProfileMenu.viewing_profile)
async def handle_profile_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "🏠 Назад":
        await state.clear()
        await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())
        return

    if text == "📦 Инвентарь":
        await state.set_state(ProfileMenu.viewing_inventory)
        await _send_inventory(message, user_id)
        return

    if text == "🎭 Статусы":
        player = get_player(user_id)
        await state.set_state(ProfileMenu.viewing_statuses)
        statuses_text = "🎭 <b>СТАТУСЫ</b>\n\nВыбери статус для своего персонажа:\n\n"
        for s_id, s in STATUSES.items():
            req_lvl = s.get('required_level', 1)
            can = (player.get('player_level', 1) >= req_lvl)
            owned = (player.get('status') == s['name'])
            lock = "" if can else f" 🔒(ур.{req_lvl})"
            check = " ✅" if owned else ""
            statuses_text += f"{s['emoji']} <b>{s['name']}</b>{lock}{check}\n"
        await message.answer(statuses_text, reply_markup=get_statuses_kb(player))
        return

    # Refresh profile
    player = get_player(user_id)
    if player:
        await _send_profile(message, player)

@dp.message(ProfileMenu.viewing_inventory)
async def handle_profile_inventory(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅️ Назад":
        player = get_player(user_id)
        await state.set_state(ProfileMenu.viewing_profile)
        if player:
            await _send_profile(message, player)
        return

    await _send_inventory(message, user_id)

@dp.message(ProfileMenu.viewing_statuses)
async def handle_profile_statuses(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text

    if text == "⬅️ Назад":
        await state.set_state(ProfileMenu.viewing_profile)
        await _send_profile(message, player)
        return

    # Check if player selected a status
    for s_id, s in STATUSES.items():
        req_lvl = s.get('required_level', 1)
        can = (player.get('player_level', 1) >= req_lvl)
        owned = (player.get('status') == s['name'])
        label_base = f"{s['emoji']} {s['name']}"
        if text.startswith(label_base):
            if owned:
                await message.answer(f"✅ Статус «{s['name']}» уже активен!", reply_markup=get_statuses_kb(player))
                return
            if not can:
                await message.answer(f"🔒 Нужен уровень {req_lvl} для этого статуса!", reply_markup=get_statuses_kb(player))
                return
            set_player_status(user_id, s['name'])
            updated = get_player(user_id)
            await message.answer(f"✅ Статус изменён на «{s['name']}» {s['emoji']}!", reply_markup=get_statuses_kb(updated))
            return

    await message.answer("Выбери статус из списка!", reply_markup=get_statuses_kb(player))

# ============== INVENTORY TAB ==============
async def _send_inventory(message, user_id: int, back_button: str = "⬅️ Назад"):
    """Показать инвентарь игрока"""
    player = get_player(user_id)
    inv = get_inventory(user_id)
    nickname = player['nickname'] if player else "Игрок"
    text = (
        f'{E_INV_BOX} <b>Инвентарь {nickname}:</b>\n\n'
        f'┃{inv["wood"]}{E_WOOD} {E_BULLET} Древесина\n'
        f'┃{inv["stone"]}{E_STONE} {E_BULLET} Камень\n'
        f'┃{inv["food"]}{E_FOOD} {E_BULLET} Еда\n'
        f'┃{inv["iron"]}{E_IRON} {E_BULLET} Железо\n'
        f'┃{inv["gold"]}{E_GOLD_M} {E_BULLET} Золото\n'
    )
    inv_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=back_button)]], resize_keyboard=True)
    await send_image_with_text(message, "images/inventory/inventory.png", text, reply_markup=inv_kb)

@dp.message(F.text == "📦 Инвентарь")
async def open_inventory_main(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    await _send_inventory(message, user_id, back_button="🏠 В главное меню")

# ============== MAP / LOCATIONS ==============
@dp.message(F.text == "🗺️ Карта")
async def open_map(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    # Check if any activity just completed
    completed = check_activity_done(user_id)
    if completed:
        monster = await _give_activity_rewards(user_id, completed)
        if not monster:
            await state.set_state(LocationMenu.viewing_map)
            map_text = "🗺️ <b>КАРТА</b>\n\nВыбери локацию для исследования:"
            await message.answer(map_text, reply_markup=get_map_kb())
        return

    activity = get_active_activity(user_id)
    if activity:
        import datetime as dt
        try:
            end_time = datetime.fromisoformat(activity['end_time'])
        except Exception:
            end_time = None
        if end_time:
            remaining = max(0, int((end_time - datetime.utcnow()).total_seconds()))
            loc = LOCATIONS.get(activity['location_id'], {})
            act_cfg = loc.get('activities', {}).get(activity['activity_type'], {})
            await message.answer(
                f"⏳ <b>Активность в процессе</b>\n\n"
                f"Локация: {loc.get('name', '?')}\n"
                f"Действие: {act_cfg.get('name', activity['activity_type'])}\n"
                f"Осталось: {remaining} сек.",
                reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Вернуться")]], resize_keyboard=True)
            )
            await state.set_state(LocationMenu.viewing_map)
            return

    map_text = "🗺️ <b>КАРТА</b>\n\nВыбери локацию для исследования:"
    await message.answer(map_text, reply_markup=get_map_kb())
    await state.set_state(LocationMenu.viewing_map)

@dp.message(LocationMenu.viewing_map)
async def handle_map(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "❌ Вернуться":
        await state.clear()
        await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())
        return

    # Check if activity completed while waiting
    completed = check_activity_done(user_id)
    if completed:
        monster = await _give_activity_rewards(user_id, completed)
        if not monster:
            map_text = "🗺️ <b>КАРТА</b>\n\nВыбери локацию для исследования:"
            await message.answer(map_text, reply_markup=get_map_kb())
        return

    for loc_id, loc in LOCATIONS.items():
        if text == loc['name']:
            await state.update_data(selected_location=loc_id)
            loc_text = f"{loc['emoji']} <b>{loc['name']}</b>\n\nВыбери действие:\n"
            for act_key, act in loc['activities'].items():
                monster_note = f"(⚠️ {int(act['monster_chance']*100)}% шанс монстра)" if act['monster_chance'] > 0 else ""
                loc_text += f"\n{act['time']}s{E_TIMER}│{act['emoji']}│{E_BULLET} {act['name']} {monster_note}\n"
            await message.answer(loc_text, reply_markup=get_location_activities_kb(loc_id))
            await state.set_state(LocationMenu.viewing_location)
            return

    await message.answer("Выбери локацию из списка!", reply_markup=get_map_kb())

@dp.message(LocationMenu.viewing_location)
async def handle_location(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    loc_id = data.get('selected_location', 1)
    loc = LOCATIONS.get(loc_id)

    if text == "⬅️ Назад на карту":
        map_text = "🗺️ <b>КАРТА</b>\n\nВыбери локацию для исследования:"
        await message.answer(map_text, reply_markup=get_map_kb())
        await state.set_state(LocationMenu.viewing_map)
        return

    if not loc:
        await state.set_state(LocationMenu.viewing_map)
        await message.answer("Локация не найдена.", reply_markup=get_map_kb())
        return

    # Check if already has active activity
    existing = get_active_activity(user_id)
    if existing:
        import datetime as dt
        try:
            end_time = datetime.fromisoformat(existing['end_time'])
        except Exception:
            end_time = None
        if end_time:
            remaining = max(0, int((end_time - datetime.utcnow()).total_seconds()))
            await message.answer(
                f"⏳ У тебя уже идёт активность! Осталось: {remaining} сек.",
                reply_markup=get_location_activities_kb(loc_id)
            )
            return

    for act_key, act in loc['activities'].items():
        btn_text = f"{act['emoji']} {act['name']} ({act['time']}с)"
        if text == btn_text:
            start_activity(user_id, act_key, loc_id, act['time'])
            await message.answer(
                f"✅ Начато: {act['name']}\n"
                f"⏱ Время: {act['time']} секунд\n"
                f"Возвращайся на карту когда время выйдет!",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="⬅️ Назад на карту")]],
                    resize_keyboard=True
                )
            )
            return

    if text == "🔍 Поиск врага (10с)":
        await state.set_state(LocationMenu.searching_enemy)
        await message.answer(
            "🔍 <b>Поиск врага...</b>\n\n⏳ Осталось 10 секунд. Подожди — кнопки заблокированы.",
            reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
        )
        asyncio.create_task(_run_enemy_search(user_id, message.chat.id))
        return

    await message.answer("Выбери действие!", reply_markup=get_location_activities_kb(loc_id))

async def _run_enemy_search(user_id: int, chat_id: int):
    """Фоновая задача: ждёт 10 секунд, затем спаунит врага и начинает бой"""
    await asyncio.sleep(10)

    player = get_player(user_id)
    if not player:
        return

    fsm_ctx = dp.fsm.resolve_context(bot, chat_id, user_id)

    # Check still in searching_enemy state (player may have somehow left)
    current_state = await fsm_ctx.get_state()
    if current_state != LocationMenu.searching_enemy.state:
        return

    enemy_cfg = get_location_enemy_for_player(player['strength'])
    enemy_strength = enemy_cfg['strength']
    enemy_health = calculate_player_health(enemy_strength)
    enemy_damage = calculate_damage(enemy_strength)

    player_clan = get_player_clan(user_id)
    clan_level = player_clan['clan_level'] if player_clan else 1
    buffed_strength = apply_clan_strength_buff(player['strength'], clan_level)
    player_health = calculate_player_health(buffed_strength)
    player_damage = calculate_damage(buffed_strength)

    reset_battle_cooldown(user_id)

    await fsm_ctx.set_state(BattleState.in_battle)
    await fsm_ctx.update_data(
        selected_enemy=None,
        location_enemy_cfg=enemy_cfg,
        player_health=player_health,
        player_damage=player_damage,
        enemy_health=enemy_health,
        enemy_damage=enemy_damage,
        player_mana=100,
        enemy_skip_turn=False,
        player_blind_turns=0,
        is_location_battle=True,
    )

    battle_info = (
        f"⚔️ <b>ВРАГ НАЙДЕН!</b>\n\n"
        f"{enemy_cfg['emoji']} {enemy_cfg['name']}\n"
        f"🩶 {enemy_health}\n"
        f"⚔️ {enemy_damage}\n\n"
        f"👤 {player['nickname']}\n"
        f"{E_HP} {player_health}\n"
        f"⚔️ {player_damage}\n"
    )
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=battle_info,
            reply_markup=get_battle_kb(),
            parse_mode="HTML"
        )
    except Exception:
        pass

@dp.message(LocationMenu.searching_enemy)
async def handle_searching_enemy(message: types.Message, state: FSMContext):
    """Блокирует все команды во время поиска врага"""
    await message.answer("⏳ Идёт поиск врага... Подожди!")


async def _give_activity_rewards(user_id: int, activity: dict) -> bool:
    """Выдать награды за завершённую активность и отправить сообщение напрямую игроку.
    Возвращает True, если встретился монстр."""
    loc_id = activity['location_id']
    act_type = activity['activity_type']
    loc = LOCATIONS.get(loc_id, {})
    act_cfg = loc.get('activities', {}).get(act_type, {})
    rewards = act_cfg.get('rewards', {})
    monster_chance = act_cfg.get('monster_chance', 0)

    finish_activity(user_id)

    # Calculate rewards
    earned = {}
    for rew_key, (min_v, max_v) in rewards.items():
        earned[rew_key] = random.randint(min_v, max_v)

    # Apply rewards
    if 'coins' in earned:
        add_coins_to_player(user_id, earned['coins'])
    exp_result = {'leveled_up': False, 'new_level': 1}
    if 'experience' in earned:
        exp_result = add_experience_to_player(user_id, earned['experience'])
    for mat in ('food', 'wood', 'stone', 'iron', 'gold'):
        if mat in earned:
            add_inventory_material(user_id, mat, earned[mat])

    # Build reward lines with custom emojis
    mat_names = {
        'food':       (E_FOOD,   'Еда'),
        'wood':       (E_WOOD,   'Древесина'),
        'stone':      (E_STONE,  'Камень'),
        'iron':       (E_IRON,   'Железо'),
        'gold':       (E_GOLD_M, 'Золото'),
        'coins':      (E_COINS,  'Монеты'),
        'experience': (E_STAR,   'Опыт'),
    }
    reward_lines = []
    for k, v in earned.items():
        emoji, name = mat_names.get(k, ('', k))
        reward_lines.append(f"{E_PLUS} {v} {emoji} {name}")

    loc_name = loc.get('name', '?')
    act_name = act_cfg.get('name', act_type)
    act_emoji = act_cfg.get('emoji', '')

    text = (
        f"{E_CHECK} <b>Активность завершена!</b>\n\n"
        f"Локация: {loc_name}\n"
        f"Действие: {act_emoji} {act_name}\n\n"
        f"{E_GIFT} <b>Награды:</b>\n"
        + "\n".join(reward_lines)
    )
    if exp_result.get('leveled_up'):
        text += f"\n\n🎉 Уровень повышен до {exp_result['new_level']}!"

    # Check monster encounter
    monster_encountered = monster_chance > 0 and random.random() < monster_chance
    if monster_encountered:
        text += "\n\n⚠️ Внимание! Ты встретил монстра!"

    try:
        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
    except Exception:
        pass

    if monster_encountered:
        try:
            fsm_ctx = dp.fsm.resolve_context(bot, user_id, user_id)
            await fsm_ctx.set_state(LocationMenu.viewing_location)
            await bot.send_message(
                chat_id=user_id,
                text="Что будешь делать?",
                reply_markup=get_monster_encounter_kb(),
                parse_mode="HTML"
            )
        except Exception:
            pass
        return True

    return False

# Handle monster from activity
@dp.message(LocationMenu.viewing_map, F.text == "⚔️ Сразиться с монстром")
@dp.message(LocationMenu.viewing_location, F.text == "⚔️ Сразиться с монстром")
async def fight_location_monster(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    selected_enemy = 1
    enemy_info = ENEMIES[selected_enemy]
    player_clan = get_player_clan(user_id)
    clan_level = player_clan['clan_level'] if player_clan else 1
    buffed_strength = apply_clan_strength_buff(player['strength'], clan_level)
    player_health = calculate_player_health(buffed_strength)
    player_damage = calculate_damage(buffed_strength)
    enemy_damage = calculate_enemy_damage(selected_enemy)
    reset_battle_cooldown(user_id)
    await state.set_state(BattleState.in_battle)
    await state.update_data(
        selected_enemy=selected_enemy,
        player_health=player_health,
        player_damage=player_damage,
        enemy_health=enemy_info['health'],
        enemy_damage=enemy_damage,
        player_mana=100,
        enemy_skip_turn=False,
        player_blind_turns=0,
    )
    mana = 100
    battle_info = (
        f"⚔️ <b>МОНСТР!</b>\n\n"
        f"☠️ {enemy_info['name']}\n"
        f"🩶 {enemy_info['health']}\n"
        f"⚔️ {enemy_damage}\n\n"
        f"👤 {player['nickname']}\n"
        f"{E_HP} {player_health}\n"
        f"⚔️ {player_damage}\n"
    )
    await message.answer(battle_info, reply_markup=get_battle_kb())

@dp.message(LocationMenu.viewing_map, F.text == "🏃 Убежать")
@dp.message(LocationMenu.viewing_location, F.text == "🏃 Убежать")
async def flee_location_monster(message: types.Message, state: FSMContext):
    await message.answer("🏃 Ты убежал от монстра!", reply_markup=get_map_kb())
    await state.set_state(LocationMenu.viewing_map)

# ============== FORGE (КУЗНЯ) ==============
def _get_weapon_info(weapon_id: int) -> dict:
    """Получить данные об оружии по id (0 = стартовое)"""
    if weapon_id == 0:
        return DEFAULT_WEAPON
    return WEAPONS.get(weapon_id, DEFAULT_WEAPON)

def _get_armor_info(armor_id: int) -> dict:
    """Получить данные о броне по id (0 = стартовая)"""
    if armor_id == 0:
        return DEFAULT_ARMOR
    return ARMOR.get(armor_id, DEFAULT_ARMOR)

@dp.message(F.text == "🔨 Кузня")
async def open_forge(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)

    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    weapon_id = get_player_weapon(user_id)
    armor_id = get_player_armor(user_id)
    weapon = _get_weapon_info(weapon_id)
    armor = _get_armor_info(armor_id)

    forge_text = (
        "🔨 <b>КУЗНЯ</b>\n\n"
        f"{E_POW} Общая сила: {int(player['strength'])}\n\n"
        f"⚔️ Оружие: {weapon['emoji']} {weapon['name']} (сила: {weapon['strength']})\n"
        f"🛡️ Броня:  {armor['emoji']} {armor['name']} (сила: {armor['strength']})\n\n"
        "Выбери раздел для улучшения:"
    )
    await message.answer(forge_text, reply_markup=get_forge_kb())
    await state.set_state(ForgeMenu.viewing_forge)

@dp.message(ForgeMenu.viewing_forge)
async def handle_forge_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text

    if text == "❌ Выход":
        await state.clear()
        await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())
        return

    if text == "⚔️ Оружие":
        weapon_id = get_player_weapon(user_id)
        weapon = _get_weapon_info(weapon_id)
        next_weapon_id = weapon_id + 1
        if next_weapon_id > max(WEAPONS.keys()):
            weapons_text = (
                "⚔️ <b>ОРУЖИЕ</b>\n\n"
                f"Текущее оружие: {weapon['emoji']} {weapon['name']} (сила: {weapon['strength']})\n"
                f"Монеты: {player['coins']}\n\n"
                "✅ Вы достигли максимума"
            )
        else:
            next_w = WEAPONS[next_weapon_id]
            weapons_text = (
                "⚔️ <b>ОРУЖИЕ</b>\n\n"
                f"Текущее оружие: {weapon['emoji']} {weapon['name']} (сила: {weapon['strength']})\n"
                f"Монеты: {player['coins']}\n\n"
                f"Следующее улучшение:\n"
                f"{next_w['emoji']} {next_w['name']} (сила: {next_w['strength']}) — {next_w['cost']} монет"
            )
        await message.answer(weapons_text, reply_markup=get_next_weapon_kb(weapon_id))
        await state.set_state(ForgeMenu.viewing_weapons)
        return

    if text == "🛡️ Броня":
        armor_id = get_player_armor(user_id)
        armor = _get_armor_info(armor_id)
        next_armor_id = armor_id + 1
        if next_armor_id > max(ARMOR.keys()):
            armor_text = (
                "🛡️ <b>БРОНЯ</b>\n\n"
                f"Текущая броня: {armor['emoji']} {armor['name']} (сила: {armor['strength']})\n"
                f"Монеты: {player['coins']}\n\n"
                "✅ Вы достигли максимума"
            )
        else:
            next_a = ARMOR[next_armor_id]
            armor_text = (
                "🛡️ <b>БРОНЯ</b>\n\n"
                f"Текущая броня: {armor['emoji']} {armor['name']} (сила: {armor['strength']})\n"
                f"Монеты: {player['coins']}\n\n"
                f"Следующее улучшение:\n"
                f"{next_a['emoji']} {next_a['name']} (сила: {next_a['strength']}) — {next_a['cost']} монет"
            )
        await message.answer(armor_text, reply_markup=get_next_armor_kb(armor_id))
        await state.set_state(ForgeMenu.viewing_armor)
        return

    if text == "✨ Скиллы":
        skills_text = '✨ <b>СКИЛЛЫ</b>\n\nМонеты: {}\n\n'.format(player['coins'])
        for skill_id, skill in SKILLS.items():
            owned = has_purchased_skill(user_id, skill_id)
            status = "✅ Куплено" if owned else f'Цена: {skill["price"]} монет'
            skills_text += (
                f'{skill["emoji"]} {skill["name"]}\n'
                f'  {skill["desc"]}\n'
                f'  Мана: {skill["mana_cost"]}{E_MANA} | {status}\n\n'
            )
        await message.answer(skills_text, reply_markup=get_skills_kb(user_id))
        await state.set_state(ForgeMenu.viewing_skills)
        return

    await message.answer("Выбери раздел!", reply_markup=get_forge_kb())

@dp.message(ForgeMenu.viewing_weapons)
async def handle_weapons_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text

    if text == "⬅️ Назад":
        # Вернуться в главное меню кузни
        weapon_id = get_player_weapon(user_id)
        armor_id = get_player_armor(user_id)
        weapon = _get_weapon_info(weapon_id)
        armor = _get_armor_info(armor_id)
        forge_text = (
            "🔨 <b>КУЗНЯ</b>\n\n"
            f"{E_POW} Общая сила: {int(player['strength'])}\n\n"
            f"⚔️ Оружие: {weapon['emoji']} {weapon['name']} (сила: {weapon['strength']})\n"
            f"🛡️ Броня:  {armor['emoji']} {armor['name']} (сила: {armor['strength']})\n\n"
            "Выбери раздел для улучшения:"
        )
        await message.answer(forge_text, reply_markup=get_forge_kb())
        await state.set_state(ForgeMenu.viewing_forge)
        return

    # Определить, какое оружие выбрал игрок (точное совпадение с текстом кнопки)
    if text == "✅ Вы достигли максимума":
        current_wid = get_player_weapon(user_id)
        await message.answer("✅ Вы уже достигли максимального уровня оружия!", reply_markup=get_next_weapon_kb(current_wid))
        return

    chosen_weapon_id = None
    for w_id, w_info in WEAPONS.items():
        btn = f"{w_info['emoji']} {w_info['name']} (сила: {w_info['strength']}) — {w_info['cost']} монет"
        if text == btn:
            chosen_weapon_id = w_id
            break

    if chosen_weapon_id is None:
        current_wid = get_player_weapon(user_id)
        await message.answer("❌ Выбери оружие из списка!", reply_markup=get_next_weapon_kb(current_wid))
        return

    current_weapon_id = get_player_weapon(user_id)
    current_weapon = _get_weapon_info(current_weapon_id)
    new_weapon = WEAPONS[chosen_weapon_id]

    if new_weapon['strength'] <= current_weapon['strength']:
        await message.answer(
            f"❌ Нельзя надеть оружие слабее или равное текущему!\n"
            f"Текущее: {current_weapon['emoji']} {current_weapon['name']} (сила: {current_weapon['strength']})",
            reply_markup=get_next_weapon_kb(current_weapon_id)
        )
        return

    if player['coins'] < new_weapon['cost']:
        await message.answer(
            f"❌ Недостаточно монет!\nТребуется: {new_weapon['cost']}\nУ вас есть: {player['coins']}",
            reply_markup=get_next_weapon_kb(current_weapon_id)
        )
        return

    # Купить оружие: сила заменяется, не суммируется
    armor_id = get_player_armor(user_id)
    armor = _get_armor_info(armor_id)
    new_weapon_strength = new_weapon['strength']
    new_total_strength = new_weapon_strength + armor['strength']
    new_coins = player['coins'] - new_weapon['cost']

    set_player_weapon(user_id, chosen_weapon_id)
    update_player_strength(user_id, new_total_strength)
    remove_coins_from_player(user_id, new_weapon['cost'])

    await message.answer(
        f"✅ Оружие улучшено!\n\n"
        f"{new_weapon['emoji']} {new_weapon['name']}\n"
        f"(⚔️) Сила оружия: {new_weapon_strength}\n"
        f"🛡️ Сила брони: {armor['strength']}\n"
        f"(⚔️) Общая сила: {int(new_total_strength)}\n\n"
        f"- {new_weapon['cost']} монет\nОсталось: {new_coins}",
        reply_markup=get_next_weapon_kb(chosen_weapon_id)
    )

@dp.message(ForgeMenu.viewing_armor)
async def handle_armor_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text

    if text == "⬅️ Назад":
        weapon_id = get_player_weapon(user_id)
        armor_id = get_player_armor(user_id)
        weapon = _get_weapon_info(weapon_id)
        armor = _get_armor_info(armor_id)
        forge_text = (
            "🔨 <b>КУЗНЯ</b>\n\n"
            f"{E_POW} Общая сила: {int(player['strength'])}\n\n"
            f"⚔️ Оружие: {weapon['emoji']} {weapon['name']} (сила: {weapon['strength']})\n"
            f"🛡️ Броня:  {armor['emoji']} {armor['name']} (сила: {armor['strength']})\n\n"
            "Выбери раздел для улучшения:"
        )
        await message.answer(forge_text, reply_markup=get_forge_kb())
        await state.set_state(ForgeMenu.viewing_forge)
        return

    # Определить, какую броню выбрал игрок (точное совпадение с текстом кнопки)
    if text == "✅ Вы достигли максимума":
        current_aid = get_player_armor(user_id)
        await message.answer("✅ Вы уже достигли максимального уровня брони!", reply_markup=get_next_armor_kb(current_aid))
        return

    chosen_armor_id = None
    for a_id, a_info in ARMOR.items():
        btn = f"{a_info['emoji']} {a_info['name']} (сила: {a_info['strength']}) — {a_info['cost']} монет"
        if text == btn:
            chosen_armor_id = a_id
            break

    if chosen_armor_id is None:
        current_aid = get_player_armor(user_id)
        await message.answer("❌ Выбери броню из списка!", reply_markup=get_next_armor_kb(current_aid))
        return

    current_armor_id = get_player_armor(user_id)
    current_armor = _get_armor_info(current_armor_id)
    new_armor = ARMOR[chosen_armor_id]

    if new_armor['strength'] <= current_armor['strength']:
        await message.answer(
            f"❌ Нельзя надеть броню слабее или равную текущей!\n"
            f"Текущая: {current_armor['emoji']} {current_armor['name']} (сила: {current_armor['strength']})",
            reply_markup=get_next_armor_kb(current_armor_id)
        )
        return

    if player['coins'] < new_armor['cost']:
        await message.answer(
            f"❌ Недостаточно монет!\nТребуется: {new_armor['cost']}\nУ вас есть: {player['coins']}",
            reply_markup=get_next_armor_kb(current_armor_id)
        )
        return

    # Купить броню: сила заменяется, не суммируется
    weapon_id = get_player_weapon(user_id)
    weapon = _get_weapon_info(weapon_id)
    new_armor_strength = new_armor['strength']
    new_total_strength = weapon['strength'] + new_armor_strength
    new_coins = player['coins'] - new_armor['cost']

    set_player_armor(user_id, chosen_armor_id)
    update_player_strength(user_id, new_total_strength)
    remove_coins_from_player(user_id, new_armor['cost'])

    await message.answer(
        f"✅ Броня улучшена!\n\n"
        f"{new_armor['emoji']} {new_armor['name']}\n"
        f"(⚔️) Сила оружия: {weapon['strength']}\n"
        f"🛡️ Сила брони: {new_armor_strength}\n"
        f"(⚔️) Общая сила: {int(new_total_strength)}\n\n"
        f"- {new_armor['cost']} монет\nОсталось: {new_coins}",
        reply_markup=get_next_armor_kb(chosen_armor_id)
    )

@dp.message(ForgeMenu.viewing_skills)
async def handle_skills_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text

    if text == "⬅️ Назад":
        weapon_id = get_player_weapon(user_id)
        armor_id = get_player_armor(user_id)
        weapon = _get_weapon_info(weapon_id)
        armor = _get_armor_info(armor_id)
        forge_text = (
            "🔨 <b>КУЗНЯ</b>\n\n"
            f"{E_POW} Общая сила: {int(player['strength'])}\n\n"
            f"⚔️ Оружие: {weapon['emoji']} {weapon['name']} (сила: {weapon['strength']})\n"
            f"🛡️ Броня:  {armor['emoji']} {armor['name']} (сила: {armor['strength']})\n\n"
            "Выбери раздел для улучшения:"
        )
        await message.answer(forge_text, reply_markup=get_forge_kb())
        await state.set_state(ForgeMenu.viewing_forge)
        return

    # Проверяем, нажал ли кнопку скилла
    for skill_id, skill in SKILLS.items():
        owned = has_purchased_skill(user_id, skill_id)
        status = "✅" if owned else f"{skill['price']} монет"
        expected = f"{skill['emoji']} {skill['name']} [{status}]"
        if text == expected:
            if owned:
                await message.answer(
                    f"✅ Скилл «{skill['name']}» уже куплен!",
                    reply_markup=get_skills_kb(user_id)
                )
                return
            if player['coins'] < skill['price']:
                await message.answer(
                    f'❌ Недостаточно монет!\nТребуется: {skill["price"]} монет\nУ вас: {player["coins"]}',
                    reply_markup=get_skills_kb(user_id)
                )
                return
            remove_coins_from_player(user_id, skill['price'])
            add_skill_purchase(user_id, skill_id)
            updated = get_player(user_id)
            await message.answer(
                f'✅ Скилл «{skill["name"]}» куплен!\n'
                f'- {skill["price"]} монет\nОсталось: {updated["coins"]} монет\n\n'
                f'{skill["desc"]}\nТребует маны: {skill["mana_cost"]}{E_MANA}',
                reply_markup=get_skills_kb(user_id)
            )
            return

    await message.answer("Выбери скилл из списка!", reply_markup=get_skills_kb(user_id))
@dp.message(F.text == "🎖️ Снаряжение")
async def open_equipment_shop(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    
    equip_text = "🎖️ <b>МАГАЗИН СНАРЯЖЕНИЯ</b>\n\n"
    equip_text += f'Твои очки: {player["points"]} {E_COINS}\n'
    equip_text += f'Твоя сила: {player["strength"]} {E_POW}\n\n'
    equip_text += "Доступное снаряжение:\n"
    
    for equip_id, equip_info in EQUIPMENT.items():
        status = "✅ (уже куплено)" if has_purchased_equipment(user_id, equip_id) else ""
        equip_text += f"\n{equip_info['emoji']} {equip_info['name']} (+{equip_info['strength']} силы) → {equip_info['cost']} очков {status}"
    
    await message.answer(equip_text, reply_markup=get_equipment_kb())
    await state.set_state(EquipmentMenu.viewing_equipment)

@dp.message(EquipmentMenu.viewing_equipment)
async def handle_equipment_purchase(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text
    
    if text == "❌ Выход":
        await state.clear()
        await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())
        return
    
    equipment_purchased = False
    
    for equip_id, equip_info in EQUIPMENT.items():
        if equip_info['name'] in text:
            if has_purchased_equipment(user_id, equip_id):
                await message.answer("❌ Вы уже купили данное снаряжение!", reply_markup=get_equipment_kb())
                return
            
            if player['points'] < equip_info['cost']:
                await message.answer(
                    f"❌ Недостаточно очков!\nТребуется: {equip_info['cost']}\nУ вас есть: {player['points']}",
                    reply_markup=get_equipment_kb()
                )
                return
            
            new_points = round(player['points'] - equip_info['cost'], 1)
            new_strength = round(player['strength'] + equip_info['strength'], 1)
            
            update_player_points(user_id, new_points)
            update_player_strength(user_id, new_strength)
            add_equipment_purchase(user_id, equip_id)
            
            await message.answer(
                f"✅ Снаряжение куплено!\n\n{equip_info['emoji']} {equip_info['name']}\n+ {equip_info['strength']} силы\n- {equip_info['cost']} очков\n\nНовая сила: {new_strength}\nОсталось очков: {new_points}",
                reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Выход")]], resize_keyboard=True)
            )
            equipment_purchased = True
            break
    
    if not equipment_purchased:
        await message.answer("❌ Выберите корректное снаряжение!", reply_markup=get_equipment_kb())

# ============== LEADERBOARD ==============
@dp.message(F.text == "🏆 Рейтинг")
async def show_leaderboard(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    
    leaderboard = get_leaderboard(10)
    
    if not leaderboard:
        await message.answer("📊 Рейтинг пуст. Прокачайся!", reply_markup=get_main_kb())
        return
    
    response = "(🏆) РЕЙТИНГ ИГРОКОВ\n\n"
    
    for index, (nickname, strength, wins, rating_pts) in enumerate(leaderboard, 1):
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"{index}."
        response += f"{medal} {nickname} — | {int(strength)}🗡️ | | {wins}🏆 | | {rating_pts}💠 |\n"
    
    await message.answer(response, reply_markup=get_main_kb())

# ============== RAID ==============
def _get_raid_floor_text(floor_id: int, enemy_info: dict) -> str:
    """Вернуть текст информации об этаже рейда"""
    return (
        f"🐉 <b>РЕЙД — Этаж {floor_id}/10</b>\n\n"
        f"{enemy_info['emoji']} {enemy_info['name']}\n"
        f"🩶 {enemy_info['health']} HP\n"
        f"⚔️ {enemy_info['base_damage']} атака\n"
        f"💰 Награда: {enemy_info['reward']} монет"
    )

@dp.message(F.text == "🐉 Рейд")
async def open_raid(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)

    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    # Проверить наличие билета рейда
    if player['raid_tickets'] <= 0:
        await message.answer(
            f"🎫 Для входа в рейд нужен билет рейда!\n\n"
            f"У тебя: {player['raid_tickets']} {E_TICKET}\n\n"
            "Билеты можно получить за победы или через события.",
            reply_markup=get_main_kb()
        )
        return

    # Снять билет
    remove_raid_ticket(user_id)

    # Применяем бафф клана
    player_clan = get_player_clan(user_id)
    clan_level = player_clan['clan_level'] if player_clan else 1
    buffed_strength = apply_clan_strength_buff(player['strength'], clan_level)

    # Рейд всегда начинается с первого этажа
    floor_id = 1
    update_player_raid_floor(user_id, 1)
    reset_battle_cooldown(user_id)

    mana = 100
    enemy_info = RAID_FLOORS[floor_id]
    player_health = calculate_player_health(buffed_strength)
    player_damage = calculate_damage(buffed_strength)
    enemy_damage = enemy_info['base_damage']

    raid_text = (
        f"{_get_raid_floor_text(floor_id, enemy_info)}\n\n"
        f"{'═' * 19}\n\n"
        f"👤 {player['nickname']}\n"
        f"{E_HP} {player_health}\n"
        f"⚔️ {player_damage}\n"
        f"{E_MANA} Мана: {mana}/100\n\n"
        f"Бой начинается! (Билет потрачен)"
    )

    await state.set_state(RaidState.in_raid)
    await state.update_data(
        raid_floor=floor_id,
        player_health=player_health,
        player_damage=player_damage,
        enemy_health=enemy_info['health'],
        enemy_damage=enemy_damage,
        player_mana=mana,
        enemy_skip_turn=False,
        player_blind_turns=0,
    )

    # Определяем, кто ходит первым
    player_goes_first = random.random() < 0.5
    if player_goes_first:
        raid_text += "\n\n🎲 Ты атакуешь первым!\nЧто ты будешь делать?"
        await message.answer(raid_text, reply_markup=get_battle_action_kb(user_id, mana))
    else:
        await message.answer(raid_text + "\n\n🎲 Враг атакует первым...",
                               reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await asyncio.sleep(2)

        enemy_hit = int(round(enemy_damage * random.uniform(0.7, 1.3)))
        new_player_health = player_health - enemy_hit

        log = (
            f"🐉 <b>РЕЙД — Этаж {floor_id}/10</b>\n\n"
            f"{enemy_info['emoji']} {enemy_info['name']} атакует!\n"
            f"{E_DMG} Урон: {enemy_hit}\n\n"
        )

        if new_player_health <= 0:
            update_player_raid_floor(user_id, 0)
            log += (f"👤 {player['nickname']} повержен!\n\n❌ <b>ВЫ ПРОИГРАЛИ!</b>\n\n"
                    f"Рекорд: {player['raid_max_floor']} этаж.")
            await message.answer(log, reply_markup=get_end_battle_kb())
            await state.clear()
            return

        log += (
            f"{'═' * 19}\n\n"
            f"👤 {player['nickname']}\n{E_HP} {new_player_health}\n⚔️ {player_damage}\n{E_MANA} Мана: {mana}/100\n\n"
            f"{enemy_info['emoji']} {enemy_info['name']}\n🩶 {enemy_info['health']}\n\n"
            "Твой ход!"
        )
        await state.update_data(player_health=new_player_health)
        await message.answer(log, reply_markup=get_battle_action_kb(user_id, mana))


@dp.message(RaidState.in_raid)
async def raid_battle_round(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    data = await state.get_data()
    action = message.text

    floor_id = data['raid_floor']
    enemy_info = RAID_FLOORS[floor_id]
    mana = data.get('player_mana', 100)
    enemy_skip_turn = data.get('enemy_skip_turn', False)
    player_blind_turns = data.get('player_blind_turns', 0)

    # Проверяем валидные действия (включая скиллы)
    valid_actions = {"🗡️ Атаковать", "Крит💥20%"}
    for sk_id, sk in SKILLS.items():
        if has_purchased_skill(user_id, sk_id):
            valid_actions.add(f"✨ Скилл {sk_id}: {sk['name']}")

    if action not in valid_actions:
        if action == "🏠 В главное меню":
            await state.clear()
            await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())
            return
        await message.answer("Выбери действие!", reply_markup=get_battle_action_kb(user_id, mana))
        return

    # Проверка cooldown (2 сек)
    if not can_battle_action(user_id):
        await message.answer("⏳ Подожди перед следующим ходом!")
        return

    log = f"🐉 <b>РЕЙД — Этаж {floor_id}/10</b> ⚔️\n\n"
    new_enemy_health = data['enemy_health']
    new_player_health = data['player_health']
    new_mana = mana
    new_enemy_skip = False
    new_player_blind = max(0, player_blind_turns - 1) if player_blind_turns > 0 else 0

    # ---- Обработка действия игрока ----
    skill_used = None
    for sk_id, sk in SKILLS.items():
        if action == f"✨ Скилл {sk_id}: {sk['name']}":
            skill_used = (sk_id, sk)
            break

    if skill_used:
        sk_id, sk = skill_used
        # Проверка маны
        if mana < sk['mana_cost']:
            await message.answer(
                f"❌ Недостаточно маны! Требуется {sk['mana_cost']}{E_MANA}",
                reply_markup=get_battle_action_kb(user_id, mana)
            )
            return
        new_mana -= sk['mana_cost']
        log += f"✨ {sk['name']}!\n"

        # 10% базовый промах
        if roll_miss():
            log += "💨 Промах! Враг уклонился\n\n"
            player_hit = 0
        elif sk_id == 1:  # Мега-молот: 70% урон + стан
            player_hit = int(round(data['player_damage'] * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            log += f"👤 {player['nickname']} наносит {player_hit} урона!\n"
            if random.random() < sk['stun_chance']:
                new_enemy_skip = True
                log += "😵 Враг оглушён и пропустит следующий ход!\n"
        elif sk_id == 2:  # Кровавое неистовство: 2x урон, -15% HP
            player_hit = int(round(data['player_damage'] * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            hp_loss = max(1, int(round(calculate_player_health(player['strength']) * sk['hp_loss_pct'])))
            new_player_health = max(1, new_player_health - hp_loss)
            log += f"🩸 Вы теряете {hp_loss} HP!\n"
            log += f"👤 {player['nickname']} наносит {player_hit} урона!\n"
        elif sk_id == 3:  # Ослепляющая вспышка: ослепление на 2 хода
            player_hit = 0
            new_player_blind = sk['blind_turns']
            log += f"🔦 Враг ослеплён на {sk['blind_turns']} хода! (-50% точности)\n"
        else:
            player_hit = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
        log += "\n"
    elif action == "Крит💥20%":
        is_crit = random.random() < 0.20
        if not is_crit:
            log += "⚔️ Промах крита! Ход пропущен!\n\n"
            # Враг атакует без ответа
            if enemy_skip_turn:
                log += f"😵 {enemy_info['emoji']} {enemy_info['name']} оглушён, пропускает ход!\n\n"
                log += (
                    f"{'═' * 19}\n\n"
                    f"👤 {player['nickname']}\n{E_HP} {new_player_health}\n⚔️ {data['player_damage']}\n{E_MANA} Мана: {new_mana}/100\n\n"
                    f"{enemy_info['emoji']} {enemy_info['name']}\n🩶 {new_enemy_health}\n\n"
                    "Что ты будешь делать?"
                )
                await message.answer(log, reply_markup=get_battle_action_kb(user_id, new_mana))
                await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health,
                                        player_mana=new_mana, enemy_skip_turn=False, player_blind_turns=new_player_blind)
                return
            enemy_hit = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
            new_player_health = int(round(new_player_health - enemy_hit))
            log += f"{enemy_info['emoji']} {enemy_info['name']} атакует (без ответа)!\n{E_DMG} Урон: {enemy_hit}\n\n"
            if new_player_health <= 0:
                floors_completed = floor_id - 1
                new_max = max(player['raid_max_floor'], floors_completed)
                if new_max > player['raid_max_floor']:
                    update_player_raid_max_floor(user_id, new_max)
                update_player_raid_floor(user_id, 0)
                log += (f"👤 {player['nickname']} повержен!\n\n❌ <b>ВЫ ПРОИГРАЛИ!</b>\n\n"
                        f"Пройдено этажей: {floors_completed}. Рекорд: {new_max}.")
                await message.answer(log, reply_markup=get_end_battle_kb())
                await state.clear()
                return
            log += (
                f"{'═' * 19}\n\n"
                f"👤 {player['nickname']}\n{E_HP} {new_player_health}\n⚔️ {data['player_damage']}\n{E_MANA} Мана: {new_mana}/100\n\n"
                f"{enemy_info['emoji']} {enemy_info['name']}\n🩶 {new_enemy_health}\n\n"
                "Что ты будешь делать?"
            )
            await message.answer(log, reply_markup=get_battle_action_kb(user_id, new_mana))
            await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health,
                                    player_mana=new_mana, enemy_skip_turn=new_enemy_skip, player_blind_turns=new_player_blind)
            return
        # Крит успешный
        if roll_miss():
            player_hit = 0
            log += "💨 Промах! Враг уклонился\n\n"
        else:
            base_dmg = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
            player_hit = base_dmg * 2
            log += f"{E_DMG} КРИТИЧЕСКИЙ УДАР!\n👤 {player['nickname']} атакует!\n{E_DMG} Урон: {player_hit}\n\n"
    else:
        # Обычная атака
        if roll_miss():
            player_hit = 0
            log += "💨 Промах! Враг уклонился\n\n"
        else:
            player_hit = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
            log += f"👤 {player['nickname']} атакует!\n{E_DMG} Урон: {player_hit}\n\n"

    new_enemy_health = int(round(new_enemy_health - player_hit))

    if new_enemy_health <= 0:
        # Победа на этаже
        reward = enemy_info['reward']
        add_coins_to_player(user_id, reward)
        update_rating_points(user_id, 5)
        if floor_id > player['raid_max_floor']:
            update_player_raid_max_floor(user_id, floor_id)
        player_clan = get_player_clan(user_id)
        if player_clan:
            add_clan_exp(player_clan['clan_id'], 10)

        log += f"{enemy_info['emoji']} {enemy_info['name']} повержен!\n\n"
        log += f"✅ <b>ЭТАЖ {floor_id} ПРОЙДЕН!</b>\n\n"
        log += f"💰 Награда: +{reward} монет\n"
        log += f"+5💠 очков рейтинга\n"
        if player_clan:
            log += f"+10 опыта клану\n"

        if floor_id == 10:
            update_player_raid_floor(user_id, 0)
            log += (
                "\n🎉 <b>ПОЗДРАВЛЯЕМ!</b>\n"
                "Ты прошёл все 10 этажей рейда!\n"
                "♦️💀 Зеркальный дух повержён!\n\n"
                "Рейд начинается заново с первого этажа."
            )
            await message.answer(log, reply_markup=get_end_battle_kb())
            await state.clear()
        else:
            next_floor = floor_id + 1
            update_player_raid_floor(user_id, next_floor)
            reset_battle_cooldown(user_id)
            log += f"\n⬆️ Переход на этаж {next_floor}..."
            await message.answer(log, reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
            await asyncio.sleep(2)

            next_enemy = RAID_FLOORS[next_floor]
            player_refreshed = get_player(user_id)
            new_p_health = calculate_player_health(player_refreshed['strength'])
            new_p_damage = calculate_damage(player_refreshed['strength'])
            next_mana = 100  # мана восстанавливается на новом этаже

            await state.update_data(
                raid_floor=next_floor,
                player_health=new_p_health,
                player_damage=new_p_damage,
                enemy_health=next_enemy['health'],
                enemy_damage=next_enemy['base_damage'],
                player_mana=next_mana,
                enemy_skip_turn=False,
                player_blind_turns=0,
            )

            next_text = (
                f"{_get_raid_floor_text(next_floor, next_enemy)}\n\n"
                f"{'═' * 19}\n\n"
                f"👤 {player_refreshed['nickname']}\n"
                f"{E_HP} {new_p_health}\n"
                f"⚔️ {new_p_damage}\n"
                f"{E_MANA} Мана: {next_mana}/100\n\n"
                "Твой ход!"
            )
            await message.answer(next_text, reply_markup=get_battle_action_kb(user_id, next_mana))
        return

    # Враг контратакует
    if enemy_skip_turn:
        log += f"😵 {enemy_info['emoji']} {enemy_info['name']} оглушён, пропускает ход!\n\n"
        enemy_hit = 0
    else:
        # Применяем ослепление если активно
        blind_extra = SKILLS[3]['miss_chance_add'] if new_player_blind > 0 else 0.0
        if roll_miss(blind_extra):
            enemy_hit = 0
            log += f"{enemy_info['emoji']} {enemy_info['name']} промахивается!\n\n"
        else:
            enemy_hit = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
            new_player_health = int(round(new_player_health - enemy_hit))
            log += f"{enemy_info['emoji']} {enemy_info['name']} контратакует!\n{E_DMG} Урон: {enemy_hit}\n\n"

    if new_player_health <= 0:
        floors_completed = floor_id - 1
        new_max = max(player['raid_max_floor'], floors_completed)
        if new_max > player['raid_max_floor']:
            update_player_raid_max_floor(user_id, new_max)
        update_player_raid_floor(user_id, 0)
        log += (f"👤 {player['nickname']} повержен!\n\n❌ <b>ВЫ ПРОИГРАЛИ!</b>\n\n"
                f"Пройдено этажей: {floors_completed}. Рекорд: {new_max}.")
        await message.answer(log, reply_markup=get_end_battle_kb())
        await state.clear()
        return

    log += (
        f"{'═' * 19}\n\n"
        f"👤 {player['nickname']}\n{E_HP} {new_player_health}\n⚔️ {data['player_damage']}\n{E_MANA} Мана: {new_mana}/100\n\n"
        f"{enemy_info['emoji']} {enemy_info['name']}\n🩶 {new_enemy_health}\n\n"
        "Что ты будешь делать?"
    )
    await message.answer(log, reply_markup=get_battle_action_kb(user_id, new_mana))
    await state.update_data(
        player_health=new_player_health,
        enemy_health=new_enemy_health,
        player_mana=new_mana,
        enemy_skip_turn=new_enemy_skip,
        player_blind_turns=new_player_blind,
    )


# ============== ENEMIES ==============
@dp.message(F.text == "⚔️ Враги")
async def show_enemies(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    
    enemies_text = "⚔️ <b>ВРАГИ</b>\n\n"
    
    for enemy_id, enemy_info in ENEMIES.items():
        enemies_text += f"{enemy_info['name']} 🩶 {enemy_info['health']} HP\n"
    
    await message.answer(enemies_text, reply_markup=get_enemies_kb())
    await state.set_state(BattleState.viewing_enemies)

@dp.message(BattleState.viewing_enemies)
async def select_enemy(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text
    
    if text == "❌ Вернуться":
        await state.clear()
        await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())
        return
    
    # Поиск врага
    selected_enemy = None
    for enemy_id, enemy_info in ENEMIES.items():
        if enemy_info['name'] in text:
            selected_enemy = enemy_id
            break
    
    if selected_enemy is None:
        await message.answer("❌ Выберите корректного врага!", reply_markup=get_enemies_kb())
        return
    
    # Применяем бафф клана
    player_clan = get_player_clan(user_id)
    clan_level = player_clan['clan_level'] if player_clan else 1
    buffed_strength = apply_clan_strength_buff(player['strength'], clan_level)

    player_health = calculate_player_health(buffed_strength)
    player_damage = calculate_damage(buffed_strength)
    enemy_info = ENEMIES[selected_enemy]
    enemy_damage = calculate_enemy_damage(selected_enemy)
    
    battle_info = (
        f"⚔️ <b>ИНФОРМАЦИЯ О БОЕ</b> ⚔️\n\n"
        f"информация об {player['nickname']}:\n"
        f"{E_HP} {player_health}\n"
        f"⚔️ {player_damage}\n\n"
        f"☠️ {enemy_info['name']}\n"
        f"🩶 {enemy_info['health']}\n"
        f"⚔️ {enemy_damage}\n"
    )
    
    await message.answer(battle_info, reply_markup=get_battle_kb())
    
    await state.set_state(BattleState.in_battle)
    await state.update_data(
        selected_enemy=selected_enemy,
        player_health=player_health,
        player_damage=player_damage,
        enemy_health=enemy_info['health'],
        enemy_damage=enemy_damage,
        player_mana=100,
        enemy_skip_turn=False,
        player_blind_turns=0,
    )

@dp.message(BattleState.in_battle, F.text == "⚔️ Начать сражение")
async def start_battle(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    data = await state.get_data()
    mana = data.get('player_mana', 100)
    reset_battle_cooldown(user_id)

    if data.get('is_location_battle'):
        loc_cfg = data['location_enemy_cfg']
        enemy_info = {
            'name': loc_cfg['name'],
            'emoji': loc_cfg.get('emoji', '☠️'),
            'health': data['enemy_health'],
            'reward': 0,
        }
    else:
        selected_enemy = data['selected_enemy']
        enemy_info = ENEMIES[selected_enemy]
    
    player_goes_first = random.random() < 0.5
    
    if player_goes_first:
        turn_text = "🎲 Победа в первом ходу! Ты атакуешь первым!\n\n"
        turn_text += f"👤 {player['nickname']}\n{E_HP} {data['player_health']}\n⚔️ {data['player_damage']}\n{E_MANA} Мана: {mana}/100\n\n"
        turn_text += f"☠️ {enemy_info['name']}\n🩶 {data['enemy_health']}\n⚔️ {data['enemy_damage']}\n\n"
        turn_text += "═══════════════════\n"
        turn_text += "Что ты будешь делать?"
        
        await message.answer(turn_text, reply_markup=get_battle_action_kb(user_id, mana))
        await state.update_data(player_goes_first=True)
        await state.set_state(BattleState.battle_round)
    else:
        await message.answer("🎲 Враг получил инициативу!\n\n☠️ Враг атакует первым...", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await asyncio.sleep(2)
        
        enemy_damage = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
        new_player_health = int(round(data['player_health'] - enemy_damage))
        
        battle_log = f"⚔️ <b>РАУНД БОЯ</b> ⚔️\n\n"
        battle_log += f"☠️ {enemy_info['name']} атакует!\n"
        battle_log += f"{E_DMG} Урон: {enemy_damage}\n\n"
        
        if new_player_health <= 0:
            battle_log += f"👤 {player['nickname']} повержен!\n\n"
            battle_log += f"❌ <b>ВЫ ПРОИГРАЛИ!</b>\n\n"
            battle_log += f"Ты был повержен {enemy_info['name']}..."
            
            await message.answer(battle_log, reply_markup=get_end_battle_kb())
            await state.clear()
            return
        
        battle_log += f"═══════════════════\n\n"
        battle_log += f"👤 {player['nickname']}\n{E_HP} {new_player_health}\n⚔️ {data['player_damage']}\n{E_MANA} Мана: {mana}/100\n\n"
        battle_log += f"☠️ {enemy_info['name']}\n🩶 {data['enemy_health']}\n⚔️ {data['enemy_damage']}\n\n"
        battle_log += f"═══════════════════\n"
        battle_log += "Твой ход!"
        
        await message.answer(battle_log, reply_markup=get_battle_action_kb(user_id, mana))
        await state.update_data(player_goes_first=False, player_health=new_player_health)
        await state.set_state(BattleState.battle_round)

@dp.message(BattleState.battle_round)
async def battle_round(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    data = await state.get_data()

    if data.get('is_location_battle'):
        loc_cfg = data['location_enemy_cfg']
        enemy_info = {
            'name': loc_cfg['name'],
            'emoji': loc_cfg.get('emoji', '☠️'),
            'health': data['enemy_health'],
            'reward': 0,
        }
    else:
        selected_enemy = data['selected_enemy']
        enemy_info = ENEMIES[selected_enemy]

    mana = data.get('player_mana', 100)
    enemy_skip_turn = data.get('enemy_skip_turn', False)
    player_blind_turns = data.get('player_blind_turns', 0)
    
    action = message.text

    valid_actions = {"🗡️ Атаковать", "Крит💥20%"}
    for sk_id, sk in SKILLS.items():
        if has_purchased_skill(user_id, sk_id):
            valid_actions.add(f"✨ Скилл {sk_id}: {sk['name']}")

    if action not in valid_actions:
        await message.answer("Выбери действие!", reply_markup=get_battle_action_kb(user_id, mana))
        return

    # Проверка cooldown (2 сек)
    if not can_battle_action(user_id):
        await message.answer("⏳ Подожди перед следующим ходом!")
        return

    new_enemy_health = data['enemy_health']
    new_player_health = data['player_health']
    new_mana = mana
    new_enemy_skip = False
    new_player_blind = max(0, player_blind_turns - 1) if player_blind_turns > 0 else 0
    battle_log = f"⚔️ <b>РАУНД БОЯ</b> ⚔️\n\n"

    # Обработка действия игрока
    skill_used = None
    for sk_id, sk in SKILLS.items():
        if action == f"✨ Скилл {sk_id}: {sk['name']}":
            skill_used = (sk_id, sk)
            break

    if skill_used:
        sk_id, sk = skill_used
        if mana < sk['mana_cost']:
            await message.answer(
                f"❌ Недостаточно маны! Требуется {sk['mana_cost']}{E_MANA}",
                reply_markup=get_battle_action_kb(user_id, mana)
            )
            return
        new_mana -= sk['mana_cost']
        battle_log += f"✨ {sk['name']}!\n"

        if roll_miss():
            battle_log += "💨 Промах! Враг уклонился\n\n"
            player_hit = 0
        elif sk_id == 1:
            player_hit = int(round(data['player_damage'] * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            battle_log += f"👤 {player['nickname']} наносит {player_hit} урона!\n"
            if random.random() < sk['stun_chance']:
                new_enemy_skip = True
                battle_log += "😵 Враг оглушён и пропустит следующий ход!\n"
        elif sk_id == 2:
            player_hit = int(round(data['player_damage'] * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            hp_loss = max(1, int(round(calculate_player_health(player['strength']) * sk['hp_loss_pct'])))
            new_player_health = max(1, new_player_health - hp_loss)
            battle_log += f"🩸 Вы теряете {hp_loss} HP!\n"
            battle_log += f"👤 {player['nickname']} наносит {player_hit} урона!\n"
        elif sk_id == 3:
            player_hit = 0
            new_player_blind = sk['blind_turns']
            battle_log += f"🔦 Враг ослеплён на {sk['blind_turns']} хода! (-50% точности)\n"
        else:
            player_hit = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
        battle_log += "\n"
    elif action == "Крит💥20%":
        is_crit = random.random() < 0.20
        if not is_crit:
            battle_log += "⚔️ Промах крита! Ход пропущен!\n\n"
            if enemy_skip_turn:
                battle_log += f"😵 {enemy_info['name']} оглушён, пропускает ход!\n\n"
                battle_log += f"═══════════════════\n\n"
                battle_log += f"👤 {player['nickname']}\n{E_HP} {new_player_health}\n⚔️ {data['player_damage']}\n{E_MANA} Мана: {new_mana}/100\n\n"
                battle_log += f"☠️ {enemy_info['name']}\n🩶 {new_enemy_health}\n\n"
                battle_log += "Что ты будешь делать?"
                await message.answer(battle_log, reply_markup=get_battle_action_kb(user_id, new_mana))
                await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health,
                                        player_mana=new_mana, enemy_skip_turn=False, player_blind_turns=new_player_blind)
                return
            enemy_damage = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
            new_player_health = int(round(new_player_health - enemy_damage))
            battle_log += f"☠️ {enemy_info['name']} атакует (без ответа)!\n{E_DMG} Урон: {enemy_damage}\n\n"
            if new_player_health <= 0:
                battle_log += f"👤 {player['nickname']} повержен!\n\n❌ <b>ВЫ ПРОИГРАЛИ!</b>\n\nТы был повержен {enemy_info['name']}..."
                await message.answer(battle_log, reply_markup=get_end_battle_kb())
                await state.clear()
                return
            battle_log += f"═══════════════════\n\n"
            battle_log += f"👤 {player['nickname']}\n{E_HP} {new_player_health}\n⚔️ {data['player_damage']}\n{E_MANA} Мана: {new_mana}/100\n\n"
            battle_log += f"☠️ {enemy_info['name']}\n🩶 {new_enemy_health}\n\n"
            battle_log += "Что ты будешь делать?"
            await message.answer(battle_log, reply_markup=get_battle_action_kb(user_id, new_mana))
            await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health,
                                    player_mana=new_mana, enemy_skip_turn=new_enemy_skip, player_blind_turns=new_player_blind)
            return
        if roll_miss():
            player_hit = 0
            battle_log += "💨 Промах! Враг уклонился\n\n"
        else:
            base_damage = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
            player_hit = base_damage * 2
            battle_log += f"{E_DMG} КРИТИЧЕСКИЙ УДАР!\n👤 {player['nickname']} атакует!\n{E_DMG} Урон: {player_hit}\n\n"
    else:
        if roll_miss():
            player_hit = 0
            battle_log += "💨 Промах! Враг уклонился\n\n"
        else:
            player_hit = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
            battle_log += f"👤 {player['nickname']} атакует!\n{E_DMG} Урон: {player_hit}\n\n"

    new_enemy_health = int(round(new_enemy_health - player_hit))

    if new_enemy_health <= 0:
        reward = enemy_info['reward']
        add_coins_to_player(user_id, reward)
        update_rating_points(user_id, 5)
        player_clan = get_player_clan(user_id)
        if player_clan:
            add_clan_exp(player_clan['clan_id'], 10)
        
        battle_log += f"☠️ {enemy_info['name']} повержен!\n\n"
        battle_log += f"✅ <b>ВЫ ПОБЕДИЛИ!</b>\n\n"
        battle_log += f"💰 Награда: +{reward} монет\n"
        battle_log += f"+5💠 очков рейтинга\n"
        
        await message.answer(battle_log, reply_markup=get_end_battle_kb())
        await state.clear()
        return
    
    # Враг контратакует
    if enemy_skip_turn:
        battle_log += f"😵 {enemy_info['name']} оглушён, пропускает ход!\n\n"
        enemy_damage_dealt = 0
    else:
        blind_extra = SKILLS[3]['miss_chance_add'] if new_player_blind > 0 else 0.0
        if roll_miss(blind_extra):
            battle_log += f"{enemy_info['name']} промахивается!\n\n"
            enemy_damage_dealt = 0
        else:
            enemy_damage_dealt = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
            new_player_health = int(round(new_player_health - enemy_damage_dealt))
            battle_log += f"☠️ {enemy_info['name']} контратакует!\n{E_DMG} Урон: {enemy_damage_dealt}\n\n"
    
    if new_player_health <= 0:
        battle_log += f"👤 {player['nickname']} повержен!\n\n❌ <b>ВЫ ПРОИГРАЛИ!</b>\n\nТы был повержен {enemy_info['name']}..."
        await message.answer(battle_log, reply_markup=get_end_battle_kb())
        await state.clear()
        return
    
    battle_log += f"═══════════════════\n\n"
    battle_log += f"👤 {player['nickname']}\n{E_HP} {new_player_health}\n⚔️ {data['player_damage']}\n{E_MANA} Мана: {new_mana}/100\n\n"
    battle_log += f"☠️ {enemy_info['name']}\n🩶 {new_enemy_health}\n\n"
    battle_log += "Что ты будешь делать?"
    
    await message.answer(battle_log, reply_markup=get_battle_action_kb(user_id, new_mana))
    await state.update_data(
        player_health=new_player_health,
        enemy_health=new_enemy_health,
        player_mana=new_mana,
        enemy_skip_turn=new_enemy_skip,
        player_blind_turns=new_player_blind,
    )

@dp.message(BattleState.in_battle, F.text == "❌ Назад")
async def back_to_enemies(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    enemies_text = "⚔️ <b>ВРАГИ</b>\n\n"
    
    for enemy_id, enemy_info in ENEMIES.items():
        enemies_text += f"{enemy_info['name']} 🩶 {enemy_info['health']} HP\n"
    
    await message.answer(enemies_text, reply_markup=get_enemies_kb())
    await state.set_state(BattleState.viewing_enemies)

@dp.message(F.text == "🏠 В главное меню")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())

# ============== ONLINE (PvP) ==============
@dp.message(F.text == "🌐 Онлайн")
async def open_online(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)

    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    if user_id in pvp_queue:
        await message.answer("Ты уже в очереди поиска!", reply_markup=get_searching_kb())
        await state.set_state(OnlineState.searching)
        return

    # Применяем бафф клана
    player_clan = get_player_clan(user_id)
    clan_level = player_clan['clan_level'] if player_clan else 1
    buffed_strength = apply_clan_strength_buff(player['strength'], clan_level)

    health = calculate_player_health(buffed_strength)
    damage = calculate_damage(buffed_strength)

    search_text = (
        f'{E_ONLINE} <b>ОНЛАЙН РЕЖИМ</b>\n\n'
        'Твои характеристики:\n'
        f'{E_NICK} {player["nickname"]}\n'
        f'{E_HP} {health}\n'
        f'{E_DMG} {damage}\n'
        f'{E_POW} {int(buffed_strength)}🗡️ | {player["wins"]}🏆\n\n'
        '🔍 Ищем соперника...'
    )

    pvp_queue[user_id] = {
        "nickname": player['nickname'],
        "strength": buffed_strength,
        "wins": player['wins'],
        "health": health,
        "damage": damage,
        "chat_id": message.chat.id
    }

    await message.answer(search_text, reply_markup=get_searching_kb())
    await state.set_state(OnlineState.searching)

    # Проверяем, есть ли ещё кто-то в очереди
    other_players = [uid for uid in pvp_queue if uid != user_id]
    if other_players:
        opponent_id = other_players[0]
        opponent_data = pvp_queue.pop(opponent_id)
        my_data = pvp_queue.pop(user_id)

        # Связываем пару
        pvp_pairs[user_id] = opponent_id
        pvp_pairs[opponent_id] = user_id

        match_text_me = (
            '✅ <b>СОПЕРНИК НАЙДЕН!</b>\n\n'
            'Ваш соперник:\n'
            f'{E_NICK} {opponent_data["nickname"]}\n'
            f'{E_HP} {opponent_data["health"]}\n'
            f'{E_DMG} {opponent_data["damage"]}\n'
            f'{E_POW} {int(opponent_data["strength"])}🗡️ | {opponent_data["wins"]}🏆\n\n'
            'Подтвердите участие!'
        )
        match_text_opp = (
            '✅ <b>СОПЕРНИК НАЙДЕН!</b>\n\n'
            'Ваш соперник:\n'
            f'{E_NICK} {my_data["nickname"]}\n'
            f'{E_HP} {my_data["health"]}\n'
            f'{E_DMG} {my_data["damage"]}\n'
            f'{E_POW} {int(my_data["strength"])}🗡️ | {my_data["wins"]}🏆\n\n'
            'Подтвердите участие!'
        )

        # Сохраняем данные для подтверждения
        # Используем FSM для текущего игрока
        await state.update_data(
            opponent_id=opponent_id,
            my_health=my_data['health'],
            my_damage=my_data['damage'],
            opp_health=opponent_data['health'],
            opp_damage=opponent_data['damage'],
            accepted=False
        )
        await state.set_state(OnlineState.waiting_accept)

        # Отправляем оппоненту через bot.send_message
        await bot.send_message(
            chat_id=opponent_data['chat_id'],
            text=match_text_opp,
            reply_markup=get_pvp_accept_kb(),
            parse_mode="HTML"
        )
        # Обновляем состояние оппонента через диспетчер
        opp_state = dp.fsm.resolve_context(bot, opponent_data['chat_id'], opponent_id)
        await opp_state.update_data(
            opponent_id=user_id,
            my_health=opponent_data['health'],
            my_damage=opponent_data['damage'],
            opp_health=my_data['health'],
            opp_damage=my_data['damage'],
            accepted=False
        )
        await opp_state.set_state(OnlineState.waiting_accept)

        await message.answer(match_text_me, reply_markup=get_pvp_accept_kb())


@dp.message(OnlineState.searching, F.text == "🚫 Прекратить поиск")
async def stop_searching(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    pvp_queue.pop(user_id, None)
    await state.clear()
    await message.answer("Поиск отменён.", reply_markup=get_main_kb())


@dp.message(OnlineState.waiting_accept)
async def handle_pvp_accept(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    opponent_id = data.get('opponent_id')

    if text == "❌ Отклонить":
        # Уведомляем оппонента
        pvp_pairs.pop(user_id, None)
        if opponent_id:
            pvp_pairs.pop(opponent_id, None)
            opp_player = get_player(opponent_id)
            if opp_player:
                opp_chat_id = None
                # Получаем chat_id оппонента через его данные
                opp_state = dp.fsm.resolve_context(bot, opponent_id, opponent_id)
                opp_data = await opp_state.get_data()
                await opp_state.clear()
                try:
                    await bot.send_message(
                        chat_id=opponent_id,
                        text="❌ Соперник отклонил игру.",
                        reply_markup=get_main_kb()
                    )
                except Exception:
                    pass
        await state.clear()
        await message.answer("Вы отклонили игру.", reply_markup=get_main_kb())
        return

    if text != "✅ Принять игру":
        await message.answer("Нажмите ✅ Принять игру или ❌ Отклонить", reply_markup=get_pvp_accept_kb())
        return

    # Игрок принял — помечаем
    await state.update_data(accepted=True)

    # Проверяем принял ли оппонент
    if opponent_id:
        opp_state = dp.fsm.resolve_context(bot, opponent_id, opponent_id)
        opp_data = await opp_state.get_data()
        opp_accepted = opp_data.get('accepted', False)

        if opp_accepted:
            # Оба приняли — стартуем бой
            player_goes_first = random.random() < 0.5
            reset_battle_cooldown(user_id)
            reset_battle_cooldown(opponent_id)

            # Для текущего игрока
            await state.update_data(
                pvp_player_health=data['my_health'],
                pvp_player_damage=data['my_damage'],
                pvp_enemy_health=data['opp_health'],
                pvp_enemy_damage=data['opp_damage'],
                pvp_goes_first=player_goes_first,
                pvp_my_turn=player_goes_first,
                pvp_my_mana=100,
                pvp_my_skip_turn=False,
                pvp_opp_blind_turns=0,
            )
            await state.set_state(OnlineState.in_pvp_battle)

            # Для оппонента (ход противоположный)
            await opp_state.update_data(
                pvp_player_health=opp_data['my_health'],
                pvp_player_damage=opp_data['my_damage'],
                pvp_enemy_health=opp_data['opp_health'],
                pvp_enemy_damage=opp_data['opp_damage'],
                pvp_goes_first=not player_goes_first,
                pvp_my_turn=not player_goes_first,
                pvp_my_mana=100,
                pvp_my_skip_turn=False,
                pvp_opp_blind_turns=0,
            )
            await opp_state.set_state(OnlineState.in_pvp_battle)

            opp_player = get_player(opponent_id)
            my_player = get_player(user_id)

            first_name = my_player['nickname'] if player_goes_first else opp_player['nickname']
            start_text = f'{E_SWORD} <b>БОЙ НАЧАЛСЯ!</b>\n\nПервым ходит: {first_name}\n'

            if player_goes_first:
                await message.answer(
                    start_text + f'\n{E_CURSOR} Твой ход!\n{E_MANA} Мана: 100/100',
                    reply_markup=get_battle_action_kb(user_id, 100)
                )
                await bot.send_message(
                    chat_id=opponent_id,
                    text=start_text + "\n⏳ Ход соперника...",
                    reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    start_text + "\n⏳ Ход соперника...",
                    reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
                )
                await bot.send_message(
                    chat_id=opponent_id,
                    text=start_text + f'\n{E_CURSOR} Твой ход!\n{E_MANA} Мана: 100/100',
                    reply_markup=get_battle_action_kb(opponent_id, 100),
                    parse_mode="HTML"
                )
        else:
            await message.answer("✅ Вы приняли. Ожидаем соперника...", reply_markup=get_pvp_accept_kb())


@dp.message(OnlineState.in_pvp_battle)
async def pvp_battle_round(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    opponent_id = data.get('opponent_id')

    if not data.get('pvp_my_turn', False):
        await message.answer("⏳ Сейчас ход соперника, подожди!", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        return

    # Проверка cooldown (2 сек)
    if not can_battle_action(user_id):
        await message.answer("⏳ Подожди перед следующим ходом!")
        return

    my_health = data['pvp_player_health']
    my_damage = data['pvp_player_damage']
    enemy_health = data['pvp_enemy_health']
    my_mana = data.get('pvp_my_mana', 100)
    my_skip_turn = data.get('pvp_my_skip_turn', False)
    opp_blind_turns = data.get('pvp_opp_blind_turns', 0)  # наш дебафф на ослепление соперника

    valid_actions = {"🗡️ Атаковать", "Крит💥20%"}
    for sk_id, sk in SKILLS.items():
        if has_purchased_skill(user_id, sk_id):
            valid_actions.add(f"✨ Скилл {sk_id}: {sk['name']}")

    if text not in valid_actions:
        await message.answer("Выбери действие!", reply_markup=get_battle_action_kb(user_id, my_mana))
        return

    battle_log = f"⚔️ <b>PvP БОЙ</b> ⚔️\n\n"
    new_my_mana = my_mana
    new_enemy_health = enemy_health
    opp_should_skip = False  # заставляем соперника пропустить ход
    opp_blind_add = 0  # добавляем ослепление сопернику

    # Обработка действия
    skill_used = None
    for sk_id, sk in SKILLS.items():
        if text == f"✨ Скилл {sk_id}: {sk['name']}":
            skill_used = (sk_id, sk)
            break

    if skill_used:
        sk_id, sk = skill_used
        if my_mana < sk['mana_cost']:
            await message.answer(
                f"❌ Недостаточно маны! Требуется {sk['mana_cost']}{E_MANA}",
                reply_markup=get_battle_action_kb(user_id, my_mana)
            )
            return
        new_my_mana -= sk['mana_cost']
        battle_log += f"✨ {sk['name']}!\n"

        if roll_miss():
            dealt = 0
            battle_log += "💨 Промах! Соперник уклонился\n\n"
        elif sk_id == 1:
            dealt = int(round(my_damage * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            battle_log += f'Ты наносишь {dealt} урона!\n'
            if random.random() < sk['stun_chance']:
                opp_should_skip = True
                battle_log += "😵 Соперник оглушён и пропустит следующий ход!\n"
        elif sk_id == 2:
            dealt = int(round(my_damage * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            hp_loss = max(1, int(round(my_health * sk['hp_loss_pct'])))
            my_health = max(1, my_health - hp_loss)
            battle_log += f'🩸 Ты теряешь {hp_loss} HP!\n'
            battle_log += f'Ты наносишь {dealt} урона!\n'
        elif sk_id == 3:
            dealt = 0
            opp_blind_add = sk['blind_turns']
            battle_log += f"🔦 Соперник ослеплён на {sk['blind_turns']} хода! (-50% точности)\n"
        else:
            dealt = int(round(my_damage * random.uniform(0.8, 1.2)))
        battle_log += "\n"
    elif text == "Крит💥20%":
        is_crit = random.random() < 0.20
        if not is_crit:
            dealt = 0
            battle_log += "⚔️ Промах крита! Ход пропущен!\n\n"
        elif roll_miss():
            dealt = 0
            battle_log += "💨 Промах! Соперник уклонился\n\n"
        else:
            base = int(round(my_damage * random.uniform(0.8, 1.2)))
            dealt = base * 2
            battle_log += f'{E_DMG} КРИТИЧЕСКИЙ УДАР!\nТы наносишь {dealt} урона!\n\n'
    else:
        if roll_miss():
            dealt = 0
            battle_log += "💨 Промах! Соперник уклонился\n\n"
        else:
            dealt = int(round(my_damage * random.uniform(0.8, 1.2)))
            battle_log += f'Ты атакуешь!\n{E_DMG} Урон: {dealt}\n\n'

    new_enemy_health = int(round(enemy_health - dealt))

    if new_enemy_health <= 0:
        update_player_wins(user_id)
        update_rating_points(user_id, 7)
        add_online_match(user_id)
        if opponent_id:
            add_online_match(opponent_id)
        winner_clan = get_player_clan(user_id)
        if winner_clan:
            add_clan_exp(winner_clan['clan_id'], 2)
        battle_log += "✅ <b>ВЫ ПОБЕДИЛИ!</b>\n(+1 победа, +7💠 рейтинга)"
        await message.answer(battle_log, reply_markup=get_end_battle_kb())
        pvp_pairs.pop(user_id, None)
        pvp_pairs.pop(opponent_id, None)
        await state.clear()

        if opponent_id:
            opp_state = dp.fsm.resolve_context(bot, opponent_id, opponent_id)
            await opp_state.clear()
            try:
                await bot.send_message(
                    chat_id=opponent_id,
                    text=f'⚔️ <b>PvP БОЙ</b> ⚔️\n\nСоперник атакует!\n{E_DMG} Урон: {dealt}\n\n❌ <b>ВЫ ПРОИГРАЛИ!</b>',
                    reply_markup=get_end_battle_kb(),
                    parse_mode="HTML"
                )
            except Exception:
                pass
        return

    # Передаём ход сопернику
    battle_log += (
        f'{E_CROWN} Ты: {E_HP} {my_health} | {E_MANA} {new_my_mana}/100\n'
        f'{E_SKULL} Соперник: {E_ESWORD} {new_enemy_health}\n\n'
        "⏳ Ход соперника..."
    )
    await message.answer(battle_log, reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
    await state.update_data(
        pvp_player_health=my_health,
        pvp_enemy_health=new_enemy_health,
        pvp_my_turn=False,
        pvp_my_mana=new_my_mana,
    )

    if opponent_id:
        opp_state = dp.fsm.resolve_context(bot, opponent_id, opponent_id)
        opp_data = await opp_state.get_data()
        # С точки зрения соперника: его pvp_player_health уменьшилось
        new_opp_player_health = int(round(opp_data.get('pvp_player_health', 0) - dealt))
        opp_mana = opp_data.get('pvp_my_mana', 100)
        opp_skip_now = opp_data.get('pvp_my_skip_turn', False) or opp_should_skip
        opp_current_blind = opp_data.get('pvp_opp_blind_turns', 0)
        new_opp_blind = max(opp_current_blind, opp_blind_add)  # устанавливаем/продлеваем ослепление

        await opp_state.update_data(
            pvp_player_health=new_opp_player_health,
            pvp_enemy_health=my_health,  # Bug fix: sync current player's HP to opponent's view
            pvp_my_turn=True,
            pvp_my_skip_turn=opp_skip_now,
            pvp_opp_blind_turns=new_opp_blind,
        )
        try:
            opp_msg = (
                f'⚔️ <b>PvP БОЙ</b> ⚔️\n\n'
                f'Соперник атакует! {E_DMG} {dealt} урона\n\n'
            )
            if opp_should_skip:
                opp_msg += "😵 Ты оглушён и пропустишь следующий ход!\n"
            if opp_blind_add > 0:
                opp_msg += f"🔦 Ты ослеплён на {opp_blind_add} хода!\n"
            opp_msg += (
                f'\n{E_CROWN} Ты: {E_HP} {new_opp_player_health} | {E_MANA} {opp_mana}/100\n'
                f'{E_SKULL} Соперник: {E_ESWORD} {my_health}\n\n'
            )
            # Bug fix: skip opponent turn immediately when opp_skip_now is True (handles both fresh stun and stored stun)
            if opp_skip_now:
                opp_msg += "😵 Ты оглушён — ход пропускается автоматически!\n"
                # Если соперник оглушён — сразу передаём ход обратно
                await opp_state.update_data(pvp_my_turn=False, pvp_my_skip_turn=False)
                await state.update_data(pvp_my_turn=True)
                opp_msg += "\n⏳ Ход пропущен! Ход вашего соперника..."
                await bot.send_message(chat_id=opponent_id, text=opp_msg,
                                       reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True),
                                       parse_mode="HTML")
                # Уведомляем текущего игрока что его ход вернулся
                await message.answer(
                    f'😵 Соперник был оглушён — его ход пропущен!\n\n'
                    f'{E_CROWN} Ты: {E_HP} {my_health} | {E_MANA} {new_my_mana}/100\n'
                    f'{E_SKULL} Соперник: {E_ESWORD} {new_enemy_health}\n\n'
                    f'{E_SWORD} Снова твой ход!',
                    reply_markup=get_battle_action_kb(user_id, new_my_mana)
                )
                return
            else:
                opp_msg += f'{E_SWORD} Твой ход!'
                await bot.send_message(
                    chat_id=opponent_id,
                    text=opp_msg,
                    reply_markup=get_battle_action_kb(opponent_id, opp_mana),
                    parse_mode="HTML"
                )
        except Exception:
            pass

# ============== CLANS ==============
def _format_clan_menu(clan: dict, leader_nickname: str) -> str:
    """Форматировать текст меню клана"""
    if clan['clan_level'] >= MAX_CLAN_LEVEL:
        exp_display = f"{clan['clan_exp']}📈 (МАКС 🧬)"
    else:
        max_exp = CLAN_LEVEL_EXP[clan['clan_level']]
        exp_display = f"{clan['clan_exp']} / {max_exp}📈"
    co_leaders = get_clan_co_leaders(clan['clan_id'])
    co_str = ", ".join(nick for _, nick in co_leaders) if co_leaders else "—"
    return (
        f"[🛡️] Клан: {clan['clan_name']}\n"
        f"[👑] Глава: {leader_nickname}\n"
        f"[⭐] Соруководители: {co_str}\n"
        f"👥 - {clan['members_count']} соклановцев\n"
        f"(Минимальный порог входа) - {clan['min_power']}⚔️\n"
        f"Уровень клана - {clan['clan_level']}🧬\n"
        f"{exp_display}\n\n"
        f"(🗒️) Описание клана:\n{clan['description'] or '—'}"
    )

@dp.message(F.text == "🛡️ Кланы")
async def open_clans(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    my_clan = get_player_clan(user_id)
    if my_clan:
        leader = get_player(my_clan['leader_id'])
        leader_name = leader['nickname'] if leader else "—"
        clan_text = _format_clan_menu(my_clan, leader_name)
        is_leader = (my_clan['leader_id'] == user_id)
        is_co_leader = not is_leader and get_clan_member_role(user_id, my_clan['clan_id']) == 'co_leader'
        await message.answer(clan_text, reply_markup=get_my_clan_kb(is_leader, is_co_leader))
        await state.set_state(ClanMenu.viewing_my_clan)
        await state.update_data(clan_id=my_clan['clan_id'])
    else:
        clans = get_all_clans()
        if clans:
            clans_text = "🛡️ <b>СПИСОК КЛАНОВ</b>\n\n"
            for clan in clans:
                _, name, lvl, members, min_power, ldr = clan
                clans_text += f"🛡️ {name} — ур.{lvl} | {members}👥 | порог: {min_power}⚔️\n"
        else:
            clans_text = "🛡️ <b>КЛАНОВ ЕЩЁ НЕТ</b>\n\nСтань первым!"
        await message.answer(clans_text, reply_markup=get_clans_list_kb(clans))
        await state.set_state(ClanMenu.viewing_clans)

@dp.message(ClanMenu.viewing_clans)
async def handle_clans_list(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text

    if text == "❌ Вернуться":
        await state.clear()
        await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())
        return

    if text == "➕ Создать клан":
        if get_player_clan(user_id):
            await message.answer("❌ Вы уже состоите в клане!", reply_markup=get_clans_list_kb(get_all_clans()))
            return
        if player['coins'] < 2000:
            await message.answer(
                f"❌ Недостаточно монет!\nТребуется: 2000💰\nУ вас: {player['coins']}💰",
                reply_markup=get_clans_list_kb(get_all_clans())
            )
            return
        await message.answer(
            "Вы хотите потратить 2000💰 монет на создание клана?",
            reply_markup=get_create_clan_confirm_kb()
        )
        await state.set_state(ClanMenu.creating_clan_confirm)
        return

    # Попытка вступить в клан по кнопке
    clans = get_all_clans()
    for clan_data in clans:
        clan_id, clan_name, clan_level, members_count, min_power, leader_name = clan_data
        expected_btn = f"🛡️ {clan_name} [ур.{clan_level}] [{members_count}👥] [{min_power}⚔️]"
        if text == expected_btn:
            if get_player_clan(user_id):
                await message.answer("❌ Вы уже состоите в клане!")
                return
            if player['strength'] < min_power:
                await message.answer(
                    f"❌ Ваша мощь недостаточна. Требуется {min_power}⚔️\nВаша мощь: {int(player['strength'])}⚔️",
                    reply_markup=get_clans_list_kb(clans)
                )
                return
            join_clan(user_id, clan_id)
            updated_clan = get_player_clan(user_id)
            leader = get_player(updated_clan['leader_id'])
            leader_name_str = leader['nickname'] if leader else "—"
            clan_text = _format_clan_menu(updated_clan, leader_name_str)
            await message.answer(f"✅ Вы вступили в {clan_name}!\n\n" + clan_text,
                                 reply_markup=get_my_clan_kb(False))
            await state.set_state(ClanMenu.viewing_my_clan)
            await state.update_data(clan_id=clan_id)
            return

    await message.answer("Выбери клан из списка или создай новый!", reply_markup=get_clans_list_kb(clans))

@dp.message(ClanMenu.creating_clan_confirm)
async def handle_create_clan_confirm(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text

    if text == "❌ Нет":
        clans = get_all_clans()
        await message.answer("Отменено.", reply_markup=get_clans_list_kb(clans))
        await state.set_state(ClanMenu.viewing_clans)
        return

    if text == "✅ Да, создать":
        if player['coins'] < 2000:
            await message.answer("❌ Недостаточно монет для создания клана!", reply_markup=get_main_kb())
            await state.clear()
            return
        remove_coins_from_player(user_id, 2000)
        await message.answer("Введите название клана:", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(ClanMenu.creating_clan_name)
        return

    await message.answer("Нажмите ✅ Да, создать или ❌ Нет", reply_markup=get_create_clan_confirm_kb())

@dp.message(ClanMenu.creating_clan_name)
async def handle_create_clan_name(message: types.Message, state: FSMContext):
    clan_name = message.text.strip()
    if not clan_name or len(clan_name) > 32:
        await message.answer("❌ Название должно быть от 1 до 32 символов. Введите ещё раз:")
        return
    await state.update_data(new_clan_name=clan_name)
    await message.answer("Введите описание клана:")
    await state.set_state(ClanMenu.creating_clan_description)

@dp.message(ClanMenu.creating_clan_description)
async def handle_create_clan_description(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    description = message.text.strip()
    data = await state.get_data()
    clan_name = data.get('new_clan_name', '')

    clan_id = create_clan(clan_name, user_id, description)
    if clan_id == -1:
        await message.answer("❌ Клан с таким названием уже существует! Попробуйте другое.")
        await state.set_state(ClanMenu.creating_clan_name)
        await message.answer("Введите название клана:")
        return

    clan = get_player_clan(user_id)
    leader = get_player(user_id)
    clan_text = _format_clan_menu(clan, leader['nickname'])
    await message.answer(f"✅ Клан создан!\n\n" + clan_text, reply_markup=get_my_clan_kb(True))
    await state.set_state(ClanMenu.viewing_my_clan)
    await state.update_data(clan_id=clan_id)

@dp.message(ClanMenu.viewing_my_clan)
async def handle_my_clan(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')

    if text == "🔙 Вернуться":
        await state.clear()
        await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())
        return

    clan = get_clan(clan_id) if clan_id else None
    if not clan:
        await state.clear()
        await message.answer("Клан не найден.", reply_markup=get_main_kb())
        return

    is_leader = (clan['leader_id'] == user_id)
    role = get_clan_member_role(user_id, clan_id)
    is_co_leader = not is_leader and role == 'co_leader'

    if text == "🚪 Выйти из клана" and not is_leader:
        leave_clan(user_id, clan_id)
        await state.clear()
        clans = get_all_clans()
        await message.answer("Вы вышли из клана.", reply_markup=get_clans_list_kb(clans))
        await state.set_state(ClanMenu.viewing_clans)
        return

    if text == "👢 Кикнуть игрока" and (is_leader or is_co_leader):
        members = get_clan_members(clan_id)
        co_leader_ids = [uid for uid, _ in get_clan_co_leaders(clan_id)]
        # co-leader cannot kick the leader or other co-leaders
        if is_co_leader:
            kickable = [(uid, nick, st, r) for uid, nick, st, r in members
                        if uid != clan['leader_id'] and uid not in co_leader_ids]
        else:
            kickable = [(uid, nick, st, r) for uid, nick, st, r in members
                        if uid != clan['leader_id']]
        if not kickable:
            await message.answer("В клане нет участников для кика.",
                                 reply_markup=get_my_clan_kb(is_leader, is_co_leader))
            return
        await message.answer("Выберите игрока для кика:",
                             reply_markup=get_kick_members_kb(members, clan['leader_id'],
                                                              co_leader_ids if is_co_leader else []))
        await state.set_state(ClanMenu.kicking_member)
        return

    if text == "⭐ Назначить соруководителя" and is_leader:
        members = get_clan_members(clan_id)
        promotable = [(uid, nick, st, r) for uid, nick, st, r in members
                      if uid != clan['leader_id'] and r != 'co_leader']
        if not promotable:
            await message.answer("Нет игроков для назначения соруководителем.",
                                 reply_markup=get_my_clan_kb(True))
            return
        await message.answer("Выберите игрока для назначения соруководителем:",
                             reply_markup=get_promote_members_kb(members, clan['leader_id']))
        await state.set_state(ClanMenu.promoting_member)
        return

    if text == "⬇️ Снять соруководителя" and is_leader:
        co_leaders = get_clan_co_leaders(clan_id)
        if not co_leaders:
            await message.answer("В клане нет соруководителей.", reply_markup=get_my_clan_kb(True))
            return
        await message.answer("Выберите соруководителя для снятия с должности:",
                             reply_markup=get_demote_members_kb(co_leaders))
        await state.set_state(ClanMenu.demoting_member)
        return

    if text == "⚙️ Изменить порог" and is_leader:
        await message.answer("Введите новый минимальный порог мощи для вступления (число):",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(ClanMenu.changing_min_power)
        return

    if text == "🗑️ Удалить клан" and is_leader:
        await message.answer("Вы уверены, что хотите удалить клан? Это действие необратимо.",
                             reply_markup=get_delete_clan_confirm_kb())
        await state.set_state(ClanMenu.deleting_clan_confirm)
        return

    if text == "🎨 Изменить оформление" and is_leader:
        kb = [
            [KeyboardButton(text="📝 Изменить название (500 монет)")],
            [KeyboardButton(text="📄 Изменить описание (500 монет)")],
            [KeyboardButton(text="🖼️ Изменить картину клана")],
            [KeyboardButton(text="❌ Отмена")],
        ]
        await message.answer(
            "🎨 <b>ИЗМЕНЕНИЕ ОФОРМЛЕНИЯ КЛАНА</b>\n\nВыберите что изменить:",
            reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        )
        await state.set_state(ClanMenu.selecting_clan_customization)
        return

    if text == "💬 Чат клана":
        import html as _html
        messages = get_clan_messages(clan_id, 30)
        if messages:
            chat_text = "💬 <b>ЧАТ КЛАНА</b> (последние 30 сообщений)\n\n"
            for nick, msg, sent_at in messages:
                time_str = sent_at[:16] if sent_at else ""
                chat_text += f"[{time_str}] <b>{_html.escape(nick)}</b>: {_html.escape(msg)}\n"
        else:
            chat_text = "💬 <b>ЧАТ КЛАНА</b>\n\nПока нет сообщений. Будь первым!"
        # Register user in active chat sessions
        if clan_id not in clan_chat_sessions:
            clan_chat_sessions[clan_id] = set()
        clan_chat_sessions[clan_id].add(user_id)
        await message.answer(chat_text + "\n\nПишите сообщения — они увидят все участники клана онлайн.\nДля выхода нажмите 🚪 Выйти из чата.",
                             reply_markup=get_clan_chat_kb())
        await state.set_state(ClanMenu.in_clan_chat)
        return

    # Обновить и показать информацию о клане
    leader = get_player(clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(clan, leader_name)
    await message.answer(clan_text, reply_markup=get_my_clan_kb(is_leader, is_co_leader))

@dp.message(ClanMenu.kicking_member)
async def handle_kick_member(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')
    clan = get_clan(clan_id) if clan_id else None

    is_leader = clan and clan['leader_id'] == user_id
    is_co_leader = clan and not is_leader and get_clan_member_role(user_id, clan_id) == 'co_leader'

    if text == "❌ Отмена" or not clan:
        if clan:
            leader = get_player(clan['leader_id'])
            leader_name = leader['nickname'] if leader else "—"
            clan_text = _format_clan_menu(clan, leader_name)
            await message.answer(clan_text, reply_markup=get_my_clan_kb(is_leader, is_co_leader))
        else:
            await message.answer("Вернулись в меню клана.", reply_markup=get_main_kb())
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    # Найти участника по нику
    members = get_clan_members(clan_id)
    co_leader_ids = [uid for uid, _ in get_clan_co_leaders(clan_id)]
    kicked = False
    for member_id, nickname, strength, role in members:
        # co-leader cannot kick other co-leaders or the leader
        if member_id == clan['leader_id']:
            continue
        if is_co_leader and member_id in co_leader_ids:
            continue
        if text == f"👤 {nickname}":
            kick_clan_member(member_id, clan_id)
            kicked = True
            clan_name = clan['clan_name']
            await message.answer(f"✅ Игрок {nickname} исключён из клана.")

            # Отправляем уведомление кикнутому игроку
            try:
                await bot.send_message(
                    chat_id=member_id,
                    text=f'Вас кикнули из клана "{clan_name}" {E_ANGRY}',
                    parse_mode="HTML"
                )
            except Exception:
                pass

            break

    if not kicked:
        await message.answer("❌ Игрок не найден!",
                             reply_markup=get_kick_members_kb(members, clan['leader_id'],
                                                              co_leader_ids if is_co_leader else []))
        return

    updated_clan = get_clan(clan_id)
    leader = get_player(updated_clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(updated_clan, leader_name)
    await message.answer(clan_text, reply_markup=get_my_clan_kb(is_leader, is_co_leader))
    await state.set_state(ClanMenu.viewing_my_clan)

@dp.message(ClanMenu.promoting_member)
async def handle_promote_member(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')
    clan = get_clan(clan_id) if clan_id else None

    if text == "❌ Отмена" or not clan:
        if clan:
            leader = get_player(clan['leader_id'])
            leader_name = leader['nickname'] if leader else "—"
            clan_text = _format_clan_menu(clan, leader_name)
            await message.answer(clan_text, reply_markup=get_my_clan_kb(True))
        else:
            await message.answer("Вернулись в меню клана.", reply_markup=get_main_kb())
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    if clan['leader_id'] != user_id:
        await message.answer("❌ Только глава может назначать соруководителей.",
                             reply_markup=get_my_clan_kb(False))
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    members = get_clan_members(clan_id)
    promoted = False
    for member_id, nickname, strength, role in members:
        if member_id != clan['leader_id'] and role != 'co_leader' and text == f"👤 {nickname}":
            set_clan_member_role(member_id, clan_id, 'co_leader')
            promoted = True
            await message.answer(f"⭐ Игрок {nickname} назначен соруководителем клана!")
            try:
                await bot.send_message(
                    chat_id=member_id,
                    text=f"⭐ Поздравляем! Вы назначены соруководителем клана «{clan['clan_name']}»!"
                )
            except Exception:
                pass
            break

    if not promoted:
        await message.answer("❌ Игрок не найден!",
                             reply_markup=get_promote_members_kb(members, clan['leader_id']))
        return

    updated_clan = get_clan(clan_id)
    leader = get_player(updated_clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(updated_clan, leader_name)
    await message.answer(clan_text, reply_markup=get_my_clan_kb(True))
    await state.set_state(ClanMenu.viewing_my_clan)

@dp.message(ClanMenu.demoting_member)
async def handle_demote_member(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')
    clan = get_clan(clan_id) if clan_id else None

    if text == "❌ Отмена" or not clan:
        if clan:
            leader = get_player(clan['leader_id'])
            leader_name = leader['nickname'] if leader else "—"
            clan_text = _format_clan_menu(clan, leader_name)
            await message.answer(clan_text, reply_markup=get_my_clan_kb(True))
        else:
            await message.answer("Вернулись в меню клана.", reply_markup=get_main_kb())
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    if clan['leader_id'] != user_id:
        await message.answer("❌ Только глава может снимать соруководителей.",
                             reply_markup=get_my_clan_kb(False))
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    co_leaders = get_clan_co_leaders(clan_id)
    demoted = False
    for co_id, co_nick in co_leaders:
        if text == f"⭐ {co_nick}":
            set_clan_member_role(co_id, clan_id, 'member')
            demoted = True
            await message.answer(f"⬇️ Игрок {co_nick} снят с должности соруководителя.")
            try:
                await bot.send_message(
                    chat_id=co_id,
                    text=f"⬇️ Вы были сняты с должности соруководителя клана «{clan['clan_name']}»."
                )
            except Exception:
                pass
            break

    if not demoted:
        await message.answer("❌ Игрок не найден!",
                             reply_markup=get_demote_members_kb(co_leaders))
        return

    updated_clan = get_clan(clan_id)
    leader = get_player(updated_clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(updated_clan, leader_name)
    await message.answer(clan_text, reply_markup=get_my_clan_kb(True))
    await state.set_state(ClanMenu.viewing_my_clan)

@dp.message(ClanMenu.in_clan_chat)
async def handle_clan_chat(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')

    if text == "🚪 Выйти из чата" or not clan_id:
        # Remove from active chat sessions
        if clan_id and clan_id in clan_chat_sessions:
            clan_chat_sessions[clan_id].discard(user_id)
        clan = get_clan(clan_id) if clan_id else None
        if clan:
            is_leader = clan['leader_id'] == user_id
            is_co_leader = not is_leader and get_clan_member_role(user_id, clan_id) == 'co_leader'
            leader = get_player(clan['leader_id'])
            leader_name = leader['nickname'] if leader else "—"
            clan_text = _format_clan_menu(clan, leader_name)
            await message.answer(clan_text, reply_markup=get_my_clan_kb(is_leader, is_co_leader))
        else:
            await message.answer("Вернулись в главное меню.", reply_markup=get_main_kb())
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    if not text:
        return

    # Validate message length
    if len(text) > CLAN_CHAT_MAX_MSG_LEN:
        await message.answer(f"❌ Сообщение слишком длинное (максимум {CLAN_CHAT_MAX_MSG_LEN} символов).",
                             reply_markup=get_clan_chat_kb())
        return

    # Get sender nickname
    player = get_player(user_id)
    if not player:
        return
    nickname = player['nickname']

    # Save to DB
    save_clan_message(clan_id, user_id, nickname, text)

    # Broadcast to all members currently in chat session
    active_members = clan_chat_sessions.get(clan_id, set()).copy()
    from datetime import datetime
    import html as _html
    time_str = datetime.now().strftime("%H:%M")
    safe_nick = _html.escape(nickname)
    safe_text = _html.escape(text)
    broadcast_text = f"[{time_str}] <b>{safe_nick}</b>: {safe_text}"
    for member_id in active_members:
        if member_id == user_id:
            continue
        try:
            await bot.send_message(chat_id=member_id, text=broadcast_text, parse_mode="HTML")
        except Exception:
            # If sending fails, remove from active sessions
            clan_chat_sessions[clan_id].discard(member_id)

@dp.message(ClanMenu.changing_min_power)
async def handle_change_min_power(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')
    clan = get_clan(clan_id) if clan_id else None

    if not clan:
        await state.clear()
        await message.answer("Клан не найден.", reply_markup=get_main_kb())
        return

    try:
        new_power = int(text)
        if new_power < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное число (≥ 0):")
        return

    set_clan_min_power(clan_id, new_power)
    updated_clan = get_clan(clan_id)
    leader = get_player(updated_clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(updated_clan, leader_name)
    await message.answer(f"✅ Порог входа обновлён: {new_power}⚔️\n\n" + clan_text,
                         reply_markup=get_my_clan_kb(True))
    await state.set_state(ClanMenu.viewing_my_clan)

@dp.message(ClanMenu.deleting_clan_confirm)
async def handle_delete_clan_confirm(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')

    if text == "❌ Нет":
        clan = get_clan(clan_id) if clan_id else None
        if clan:
            leader = get_player(clan['leader_id'])
            leader_name = leader['nickname'] if leader else "—"
            clan_text = _format_clan_menu(clan, leader_name)
            await message.answer(clan_text, reply_markup=get_my_clan_kb(True))
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    if text == "✅ Да, удалить":
        clan = get_clan(clan_id) if clan_id else None
        if clan and clan['leader_id'] == user_id:
            clan_name = clan['clan_name']
            delete_clan(clan_id)
            await state.clear()
            clans = get_all_clans()
            await message.answer(f"✅ Клан «{clan_name}» удалён.", reply_markup=get_clans_list_kb(clans))
            await state.set_state(ClanMenu.viewing_clans)
        else:
            await state.clear()
            await message.answer("❌ Ошибка при удалении клана.", reply_markup=get_main_kb())
        return

    await message.answer("Нажмите ✅ Да, удалить или ❌ Нет", reply_markup=get_delete_clan_confirm_kb())

# ============== CLAN CUSTOMIZATION ==============
async def _show_clan_info(message, clan: dict, is_leader: bool, is_co_leader: bool = False):
    """Отправить информацию о клане с картиной если есть"""
    leader = get_player(clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(clan, leader_name)
    kb = get_my_clan_kb(is_leader, is_co_leader)
    if clan.get('clan_image'):
        try:
            await message.answer_photo(clan['clan_image'], caption=clan_text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.answer(clan_text, reply_markup=kb)

@dp.message(ClanMenu.selecting_clan_customization)
async def handle_select_clan_customization(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')
    clan = get_clan(clan_id) if clan_id else None

    if not clan or clan['leader_id'] != user_id:
        await state.set_state(ClanMenu.viewing_my_clan)
        await message.answer("❌ Ошибка доступа.", reply_markup=get_my_clan_kb(False))
        return

    if text == "❌ Отмена":
        await _show_clan_info(message, clan, True)
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    player = get_player(user_id)

    if text == "📝 Изменить название (500 монет)":
        if player['coins'] < 500:
            await message.answer(f"❌ Недостаточно монет! Нужно 500, у вас {player['coins']}.")
            return
        await message.answer(
            "Введите новое название клана (1-32 символа):",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)
        )
        await state.set_state(ClanMenu.changing_clan_name)
        return

    if text == "📄 Изменить описание (500 монет)":
        if player['coins'] < 500:
            await message.answer(f"❌ Недостаточно монет! Нужно 500, у вас {player['coins']}.")
            return
        await message.answer(
            "Введите новое описание клана:",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)
        )
        await state.set_state(ClanMenu.changing_clan_description)
        return

    if text == "🖼️ Изменить картину клана":
        await message.answer(
            "Отправьте фото (JPEG или PNG) для клана:",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)
        )
        await state.set_state(ClanMenu.changing_clan_image)
        return

    kb = [
        [KeyboardButton(text="📝 Изменить название (500 монет)")],
        [KeyboardButton(text="📄 Изменить описание (500 монет)")],
        [KeyboardButton(text="🖼️ Изменить картину клана")],
        [KeyboardButton(text="❌ Отмена")],
    ]
    await message.answer("Выберите действие:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@dp.message(ClanMenu.changing_clan_name)
async def handle_clan_name_change(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')

    if text == "❌ Отмена":
        clan = get_clan(clan_id)
        if clan:
            await _show_clan_info(message, clan, True)
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    new_name = text.strip()
    if not new_name or len(new_name) > 32:
        await message.answer("❌ Название должно быть от 1 до 32 символов. Введите ещё раз:")
        return

    player = get_player(user_id)
    if player['coins'] < 500:
        clan = get_clan(clan_id)
        await message.answer("❌ Недостаточно монет!")
        if clan:
            await _show_clan_info(message, clan, True)
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    success = update_clan_name(clan_id, new_name)
    if not success:
        await message.answer("❌ Клан с таким названием уже существует! Введите другое:")
        return

    remove_coins_from_player(user_id, 500)
    updated_clan = get_clan(clan_id)
    await message.answer(f"✅ Название клана изменено на «{new_name}»!\n- 500 монет")
    await _show_clan_info(message, updated_clan, True)
    await state.set_state(ClanMenu.viewing_my_clan)

@dp.message(ClanMenu.changing_clan_description)
async def handle_clan_description_change(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')

    if text == "❌ Отмена":
        clan = get_clan(clan_id)
        if clan:
            await _show_clan_info(message, clan, True)
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    player = get_player(user_id)
    if player['coins'] < 500:
        clan = get_clan(clan_id)
        await message.answer("❌ Недостаточно монет!")
        if clan:
            await _show_clan_info(message, clan, True)
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    description = text.strip()
    update_clan_description(clan_id, description)
    remove_coins_from_player(user_id, 500)
    updated_clan = get_clan(clan_id)
    await message.answer("✅ Описание клана обновлено!\n- 500 монет")
    await _show_clan_info(message, updated_clan, True)
    await state.set_state(ClanMenu.viewing_my_clan)

@dp.message(ClanMenu.changing_clan_image)
async def handle_clan_image_change(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    clan_id = data.get('clan_id')

    if message.text == "❌ Отмена":
        clan = get_clan(clan_id)
        if clan:
            await _show_clan_info(message, clan, True)
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    if not message.photo:
        await message.answer("❌ Отправьте фото! Или нажмите ❌ Отмена.")
        return

    photo_file_id = message.photo[-1].file_id
    update_clan_image(clan_id, photo_file_id)
    updated_clan = get_clan(clan_id)
    await message.answer("✅ Картина клана обновлена!")
    await _show_clan_info(message, updated_clan, True)
    await state.set_state(ClanMenu.viewing_my_clan)

# ============== ADMIN PANEL ==============
@dp.message(Command("67"))
async def open_admin_panel(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())
    await state.set_state(AdminPanel.main_menu)

@dp.message(AdminPanel.main_menu)
async def admin_menu_handler(message: types.Message, state: FSMContext):
    text = message.text
    if text == "❌ Выход":
        await state.clear()
        await message.answer("Вышли из админ панели.", reply_markup=get_main_kb())
        return
    if text == "💰 Накрутить монеты":
        await message.answer("Введите никнейм игрока:",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(AdminPanel.adding_coins_nickname)
        return
    if text == "💪 Накрутить силу":
        await message.answer("Введите никнейм игрока:",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(AdminPanel.adding_strength_nickname)
        return
    if text == "⭐️ Накрутить опыт":
        await message.answer("Введите никнейм игрока:",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(AdminPanel.adding_experience_nickname)
        return
    if text == "💎 Накрутить кристаллы":
        await message.answer("Введите никнейм игрока:",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(AdminPanel.adding_crystals_nickname)
        return
    if text == "📕 Накрутить билеты рейда":
        await message.answer("Введите никнейм игрока:",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(AdminPanel.adding_raid_tickets_nickname)
        return
    if text == "🥕 Накрутить материалы":
        await message.answer("Введите никнейм игрока:",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(AdminPanel.adding_materials_nickname)
        return
    await message.answer("Выберите действие!", reply_markup=get_admin_kb())

@dp.message(AdminPanel.adding_coins_nickname)
async def admin_coins_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"❌ Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите сумму монет для добавления:")
    await state.set_state(AdminPanel.adding_coins_amount)

@dp.message(AdminPanel.adding_coins_amount)
async def admin_coins_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректное число:")
        return
    data = await state.get_data()
    add_coins_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount} монет добавлено игроку {data['target_nickname']}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

@dp.message(AdminPanel.adding_strength_nickname)
async def admin_strength_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"❌ Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите сумму силы для добавления:")
    await state.set_state(AdminPanel.adding_strength_amount)

@dp.message(AdminPanel.adding_strength_amount)
async def admin_strength_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректное число:")
        return
    data = await state.get_data()
    add_strength_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount}⚔️ силы добавлено игроку {data['target_nickname']}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

@dp.message(AdminPanel.adding_experience_nickname)
async def admin_experience_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"❌ Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите количество опыта для добавления:")
    await state.set_state(AdminPanel.adding_experience_amount)

@dp.message(AdminPanel.adding_experience_amount)
async def admin_experience_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректное число:")
        return
    data = await state.get_data()
    result = add_experience_to_player(data['target_user_id'], amount)
    lvl_msg = f" (уровень повышен до {result['new_level']}!)" if result.get('leveled_up') else ""
    await message.answer(f"✅ {amount} опыта добавлено игроку {data['target_nickname']}{lvl_msg}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

@dp.message(AdminPanel.adding_crystals_nickname)
async def admin_crystals_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"❌ Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите количество кристаллов для добавления:")
    await state.set_state(AdminPanel.adding_crystals_amount)

@dp.message(AdminPanel.adding_crystals_amount)
async def admin_crystals_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректное число:")
        return
    data = await state.get_data()
    add_crystals_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount} кристаллов добавлено игроку {data['target_nickname']}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

@dp.message(AdminPanel.adding_raid_tickets_nickname)
async def admin_raid_tickets_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"❌ Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите количество билетов рейда для добавления:")
    await state.set_state(AdminPanel.adding_raid_tickets_amount)

@dp.message(AdminPanel.adding_raid_tickets_amount)
async def admin_raid_tickets_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректное число:")
        return
    data = await state.get_data()
    add_raid_tickets_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount} билетов рейда добавлено игроку {data['target_nickname']}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

@dp.message(AdminPanel.adding_materials_nickname)
async def admin_materials_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"❌ Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите количество материалов для добавления (каждого вида):")
    await state.set_state(AdminPanel.adding_materials_amount)

@dp.message(AdminPanel.adding_materials_amount)
async def admin_materials_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректное число:")
        return
    data = await state.get_data()
    add_admin_materials_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount} каждого материала добавлено игроку {data['target_nickname']}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

async def activity_monitor_loop():
    """Фоновая задача: проверяет завершение активностей и отправляет награды"""
    while True:
        await asyncio.sleep(10)
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM active_activities')
            user_ids = [row[0] for row in cursor.fetchall()]
            conn.close()

            now = datetime.utcnow()
            for uid in user_ids:
                activity = get_active_activity(uid)
                if not activity:
                    continue
                try:
                    end_time = datetime.fromisoformat(activity['end_time'])
                except Exception:
                    continue
                if now >= end_time:
                    await _give_activity_rewards(uid, activity)
        except Exception as e:
            import logging
            logging.error(f"Activity monitor error: {e}")

# ============== MAIN ==============
async def main():
    init_database()
    asyncio.create_task(activity_monitor_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")

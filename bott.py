import asyncio
import logging
import os
import sqlite3
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

# Ваш токен от BotFather
TOKEN = "Ваш токен"

# Прокси (опционально). Установите URL прокси для подключения без VPN,
# например: "socks5://user:pass@host:port" или "http://user:pass@host:port".
# Оставьте None чтобы не использовать прокси.
PROXY_URL = None

# ID администратора (Telegram user_id). Установите свой ID для доступа к /adminpanel672030
ADMIN_ID = 0

# Директория с картинками меню
IMAGES_DIR = "images"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

_session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else None
bot = Bot(token=TOKEN, session=_session) if _session else Bot(token=TOKEN)
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
    ]:
        try:
            cursor.execute(col_sql)
            conn.commit()
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logging.warning(f"Migration warning: {e}")
    
    # Таблица покупок улучшений клика
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS click_upgrades (
            user_id INTEGER NOT NULL,
            upgrade_id INTEGER NOT NULL,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, upgrade_id),
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )
    ''')
    
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
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, clan_id),
            FOREIGN KEY (user_id) REFERENCES players(user_id),
            FOREIGN KEY (clan_id) REFERENCES clans(clan_id)
        )
    ''')

    # Таблица статистики кланов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clan_stats (
            clan_id INTEGER PRIMARY KEY,
            total_wins INTEGER DEFAULT 0,
            total_enemies_defeated INTEGER DEFAULT 0,
            FOREIGN KEY (clan_id) REFERENCES clans(clan_id)
        )
    ''')

    conn.commit()
    conn.close()

def add_player(user_id: int, nickname: str):
    """Добавить нового игрока в БД"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO players (user_id, nickname, points, click_power, strength, wins, materials, raid_floor, raid_max_floor)
            VALUES (?, ?, 0.0, 1.0, 20.0, 0, 0, 1, 0)
        ''', (user_id, nickname))
        cursor.execute('''
            INSERT OR IGNORE INTO player_weapons (user_id, weapon_id) VALUES (?, 0)
        ''', (user_id,))
        cursor.execute('''
            INSERT OR IGNORE INTO player_armor (user_id, armor_id) VALUES (?, 0)
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
               COALESCE(materials, 0), COALESCE(raid_floor, 1), COALESCE(raid_max_floor, 0) FROM players
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

def update_click_power(user_id: int, new_power: float):
    """Обновить мощь клика"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE players 
        SET click_power = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (new_power, user_id))
    
    conn.commit()
    conn.close()

def update_last_click(user_id: int):
    """Обновить время последнего клика"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE players 
        SET last_click = CURRENT_TIMESTAMP
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

def add_click_power_to_player(user_id: int, amount: float):
    """Добавить мощь клика игроку"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET click_power = click_power + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()

def has_purchased_click_upgrade(user_id: int, upgrade_id: int) -> bool:
    """Проверить, купил ли игрок это улучшение клика"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 1 FROM click_upgrades
        WHERE user_id = ? AND upgrade_id = ?
    ''', (user_id, upgrade_id))
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

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

def add_click_upgrade_purchase(user_id: int, upgrade_id: int):
    """Добавить запись о покупке улучшения клика"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO click_upgrades (user_id, upgrade_id)
        VALUES (?, ?)
    ''', (user_id, upgrade_id))
    
    conn.commit()
    conn.close()

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
               c.clan_level, c.clan_exp, c.members_count
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
            "members_count": result[7]
        }
    return None

def get_clan(clan_id: int):
    """Получить клан по ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT clan_id, clan_name, leader_id, description, min_power,
               clan_level, clan_exp, members_count
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
            "members_count": result[7]
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
    """Получить список членов клана"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.user_id, p.nickname, p.strength
        FROM players p
        JOIN clan_members cm ON p.user_id = cm.user_id
        WHERE cm.clan_id = ?
    ''', (clan_id,))
    results = cursor.fetchall()
    conn.close()
    return results

# ============== UPGRADES ==============
UPGRADES = {
    1:  {"power": 2.0,   "cost": 20,    "display": "💳 2 клика"},
    2:  {"power": 4.0,   "cost": 100,   "display": "💳 4 клика"},
    3:  {"power": 8.0,   "cost": 250,   "display": "💳 8 клика"},
    4:  {"power": 12.0,  "cost": 550,   "display": "💳 12 клика"},
    5:  {"power": 25.0,  "cost": 1150,  "display": "💳 25 клика"},
    6:  {"power": 30.0,  "cost": 2100,  "display": "💳 30 клика"},
    7:  {"power": 40.0,  "cost": 3850,  "display": "💳 40 клика"},
    8:  {"power": 60.0,  "cost": 5200,  "display": "💳 60 клика"},
    9:  {"power": 80.0,  "cost": 9000,  "display": "💳 80 клика"},
    10: {"power": 120.0, "cost": 17000, "display": "💳 120 клика"},
}

UPGRADES_PAGE1 = {k: v for k, v in UPGRADES.items() if k <= 5}
UPGRADES_PAGE2 = {k: v for k, v in UPGRADES.items() if k > 5}

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

class ShopMenu(StatesGroup):
    viewing_shop = State()

class EquipmentMenu(StatesGroup):
    viewing_equipment = State()

class ForgeMenu(StatesGroup):
    viewing_forge = State()
    viewing_weapons = State()
    viewing_armor = State()

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

class AdminPanel(StatesGroup):
    main_menu = State()
    adding_coins_nickname = State()
    adding_coins_amount = State()
    adding_strength_nickname = State()
    adding_strength_amount = State()
    adding_click_power_nickname = State()
    adding_click_power_amount = State()

# Словарь для отслеживания cooldown клика
click_cooldowns = {}

# Очередь поиска PvP: user_id -> {nickname, strength, wins, chat_id}
pvp_queue: dict = {}
# Активные PvP пары: user_id -> opponent_user_id
pvp_pairs: dict = {}

# ============== KEYBOARDS ==============
def get_main_kb():
    """Главное меню"""
    kb = [
        [KeyboardButton(text="качать хуй")],
        [KeyboardButton(text="🏪 Магазин"), KeyboardButton(text="🔨 Кузня")],
        [KeyboardButton(text="🐉 Рейд"), KeyboardButton(text="🌐 Онлайн")],
        [KeyboardButton(text="🛡️ Кланы"), KeyboardButton(text="🏆 Рейтинг")],
        [KeyboardButton(text="📖 Профиль")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_shop_kb(page: int = 1):
    """Меню магазина (постраничное)"""
    kb = []
    items = UPGRADES_PAGE1 if page == 1 else UPGRADES_PAGE2
    for upgrade_id, upgrade_info in items.items():
        button_text = f"💲 {upgrade_info['display']} ({upgrade_info['cost']} очков)"
        kb.append([KeyboardButton(text=button_text)])
    nav = []
    if page == 2:
        nav.append(KeyboardButton(text="◀️ Предыдущая"))
    if page == 1:
        nav.append(KeyboardButton(text="Следующая ▶️"))
    if nav:
        kb.append(nav)
    kb.append([KeyboardButton(text="❌ Выход")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_forge_kb():
    """Главное меню кузни"""
    kb = [
        [KeyboardButton(text="⚔️ Оружие"), KeyboardButton(text="🛡️ Броня")],
        [KeyboardButton(text="❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_weapons_kb():
    """Меню выбора оружия"""
    kb = []
    for w_id, w_info in WEAPONS.items():
        btn = f"{w_info['emoji']} {w_info['name']} (сила: {w_info['strength']}) — {w_info['cost']} оч."
        kb.append([KeyboardButton(text=btn)])
    kb.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_armor_kb():
    """Меню выбора брони"""
    kb = []
    for a_id, a_info in ARMOR.items():
        btn = f"{a_info['emoji']} {a_info['name']} (сила: {a_info['strength']}) — {a_info['cost']} оч."
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

def get_battle_action_kb():
    """Меню действий в бою"""
    kb = [
        [KeyboardButton(text="🗡️ Атаковать")],
        [KeyboardButton(text="Крит💥20%")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_end_battle_kb():
    """Меню после боя"""
    kb = [
        [KeyboardButton(text="🏠 В главное меню")]
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
        btn = f"{w['emoji']} {w['name']} (сила: {w['strength']}) — {w['cost']} оч."
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
        btn = f"{a['emoji']} {a['name']} (сила: {a['strength']}) — {a['cost']} оч."
        kb = [
            [KeyboardButton(text=btn)],
            [KeyboardButton(text="⬅️ Назад")]
        ]
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

def get_create_clan_confirm_kb() -> ReplyKeyboardMarkup:
    """Подтверждение создания клана"""
    kb = [
        [KeyboardButton(text="✅ Да, создать")],
        [KeyboardButton(text="❌ Нет")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_my_clan_kb(is_leader: bool) -> ReplyKeyboardMarkup:
    """Меню своего клана"""
    kb = []
    if is_leader:
        kb.append([KeyboardButton(text="👢 Кикнуть игрока")])
        kb.append([KeyboardButton(text="⚙️ Изменить порог")])
        kb.append([KeyboardButton(text="🗑️ Удалить клан")])
    else:
        kb.append([KeyboardButton(text="🚪 Выйти из клана")])
    kb.append([KeyboardButton(text="🔙 Вернуться")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_kick_members_kb(members: list, leader_id: int) -> ReplyKeyboardMarkup:
    """Клавиатура со списком членов для кика"""
    kb = []
    for user_id, nickname, strength in members:
        if user_id != leader_id:
            kb.append([KeyboardButton(text=f"👤 {nickname}")])
    kb.append([KeyboardButton(text="❌ Отмена")])
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
        [KeyboardButton(text="⚡️ Накрутить мощь клика")],
        [KeyboardButton(text="❌ Выход")],
    ]
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

def can_click(user_id: int) -> bool:
    """Проверить, может ли пользователь нажать кнопку клика"""
    now = datetime.now()
    
    if user_id not in click_cooldowns:
        click_cooldowns[user_id] = now
        return True
    
    last_click = click_cooldowns[user_id]
    if (now - last_click).total_seconds() >= 1.0:
        click_cooldowns[user_id] = now
        return True
    
    return False

async def send_image_with_text(message, image_name: str, text: str, reply_markup=None):
    """Отправить картинку с текстом. Если картинка не найдена — только текст."""
    image_path = os.path.join(IMAGES_DIR, image_name)
    if os.path.exists(image_path):
        try:
            photo = FSInputFile(image_path)
            await message.answer_photo(photo, caption=text, reply_markup=reply_markup)
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=reply_markup)

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

# ============== CLICKING LOGIC ==============
@dp.message(F.text == "качать хуй")
async def clicker_logic(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Сначала напиши /start, чтобы зарегистрироваться.")
        return
    
    if not can_click(user_id):
        await message.answer("⏳ Подожди 1 секунду перед следующим кликом!")
        return
    
    new_points = round(player["points"] + player["click_power"], 1)
    update_player_points(user_id, new_points)
    update_last_click(user_id)
    
    material_found = random.random() < 0.01
    if material_found:
        new_materials = player["materials"] + 1
        update_player_materials(user_id, new_materials)
        response = (
            f"Прогресс пошел! 💪\n+ 📈 {player['click_power']}\n"
            f"Текущие очки: {new_points}🔸\n\n"
            f"⚙️ Найден материал! Всего: {new_materials}"
        )
    else:
        response = f"Прогресс пошел! 💪\n+ 📈 {player['click_power']}\nТекущие очки: {new_points}🔸"
    
    await message.answer(response)

# ============== PROFILE ==============
@dp.message(Command("профиль"))
@dp.message(F.text == "/профиль")
@dp.message(F.text == "📖 Профиль")
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Профиль не найден. Напиши /start")
        return
    
    health = calculate_player_health(player['strength'])
    damage = calculate_damage(player['strength'])
    
    response = (
        f"[🗒️] Профиль игрока: {player['nickname']}\n"
        f"🔸- Очки: {player['points']}\n"
        f"💠- Рейтинг: {player['rating_points']}\n"
        f"⚡️- Мощь клика: {player['click_power']}\n"
        f"⚙️ Материалов: {player['materials']}\n"
        f"🗼 Рекорд рейда: {player['raid_max_floor']} этаж\n\n"
        f"(⚔️) Сила: {int(player['strength'])}\n"
        f"(❤️) Здоровье: {health}\n"
        f"(💥) Урон: {damage}"
    )
    await send_image_with_text(message, "profile.png", response, reply_markup=get_main_kb())

# ============== CLICK UPGRADES SHOP ==============
@dp.message(F.text == "🏪 Магазин")
async def open_shop(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    
    await state.set_state(ShopMenu.viewing_shop)
    await state.update_data(shop_page=1)
    await _send_shop_page(message, user_id, player, 1)

async def _send_shop_page(message, user_id: int, player, page: int):
    items = UPGRADES_PAGE1 if page == 1 else UPGRADES_PAGE2
    page_label = "Страница 1" if page == 1 else "Страница 2"
    shop_text = f"🏪 **МАГАЗИН УЛУЧШЕНИЙ КЛИКА** ({page_label})\n\n"
    shop_text += f"Твои очки: {player['points']} 🔸 | Мощь клика: {player['click_power']} ⚡\n\n"
    shop_text += "Доступные улучшения:\n"
    for upgrade_id, upgrade_info in items.items():
        status = "✅" if has_purchased_click_upgrade(user_id, upgrade_id) else ""
        shop_text += f"\n{upgrade_info['display']} → {upgrade_info['cost']} очков {status}"
    await send_image_with_text(message, "shop.png", shop_text, reply_markup=get_shop_kb(page))

@dp.message(ShopMenu.viewing_shop)
async def handle_shop_purchase(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text
    data = await state.get_data()
    page = data.get('shop_page', 1)
    
    if text == "❌ Выход":
        await state.clear()
        await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())
        return

    if text == "Следующая ▶️":
        await state.update_data(shop_page=2)
        await _send_shop_page(message, user_id, player, 2)
        return

    if text == "◀️ Предыдущая":
        await state.update_data(shop_page=1)
        await _send_shop_page(message, user_id, player, 1)
        return
    
    upgrade_purchased = False
    
    for upgrade_id, upgrade_info in UPGRADES.items():
        if upgrade_info['display'] in text:
            if has_purchased_click_upgrade(user_id, upgrade_id):
                await message.answer("❌ Вы уже купили данное улучшение!", reply_markup=get_shop_kb(page))
                return
            
            if player['points'] < upgrade_info['cost']:
                await message.answer(
                    f"❌ Недостаточно очков!\nТребуется: {upgrade_info['cost']}\nУ вас есть: {player['points']}",
                    reply_markup=get_shop_kb(page)
                )
                return
            
            new_points = round(player['points'] - upgrade_info['cost'], 1)
            new_click_power = round(player['click_power'] + upgrade_info['power'], 1)
            
            update_player_points(user_id, new_points)
            update_click_power(user_id, new_click_power)
            add_click_upgrade_purchase(user_id, upgrade_id)
            
            await message.answer(
                f"✅ Улучшение куплено!\n\n+ {upgrade_info['power']} мощи клика\n- {upgrade_info['cost']} очков\n\nНовая мощь клика: {new_click_power}\nОсталось очков: {new_points}",
                reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Выход")]], resize_keyboard=True)
            )
            upgrade_purchased = True
            break
    
    if not upgrade_purchased:
        await message.answer("❌ Выберите корректное улучшение!", reply_markup=get_shop_kb(page))

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
        "🔨 **КУЗНЯ**\n\n"
        f"💪 Общая сила: {int(player['strength'])}\n\n"
        f"⚔️ Оружие: {weapon['emoji']} {weapon['name']} (сила: {weapon['strength']})\n"
        f"🛡️ Броня:  {armor['emoji']} {armor['name']} (сила: {armor['strength']})\n\n"
        "Выбери раздел для улучшения:"
    )
    await send_image_with_text(message, "kusnya.png", forge_text, reply_markup=get_forge_kb())
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
                "⚔️ **ОРУЖИЕ**\n\n"
                f"Текущее оружие: {weapon['emoji']} {weapon['name']} (сила: {weapon['strength']})\n"
                f"Очки: {player['points']}\n\n"
                "✅ Вы достигли максимума"
            )
        else:
            next_w = WEAPONS[next_weapon_id]
            weapons_text = (
                "⚔️ **ОРУЖИЕ**\n\n"
                f"Текущее оружие: {weapon['emoji']} {weapon['name']} (сила: {weapon['strength']})\n"
                f"Очки: {player['points']}\n\n"
                f"Следующее улучшение:\n"
                f"{next_w['emoji']} {next_w['name']} (сила: {next_w['strength']}) — {next_w['cost']} оч."
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
                "🛡️ **БРОНЯ**\n\n"
                f"Текущая броня: {armor['emoji']} {armor['name']} (сила: {armor['strength']})\n"
                f"Очки: {player['points']}\n\n"
                "✅ Вы достигли максимума"
            )
        else:
            next_a = ARMOR[next_armor_id]
            armor_text = (
                "🛡️ **БРОНЯ**\n\n"
                f"Текущая броня: {armor['emoji']} {armor['name']} (сила: {armor['strength']})\n"
                f"Очки: {player['points']}\n\n"
                f"Следующее улучшение:\n"
                f"{next_a['emoji']} {next_a['name']} (сила: {next_a['strength']}) — {next_a['cost']} оч."
            )
        await message.answer(armor_text, reply_markup=get_next_armor_kb(armor_id))
        await state.set_state(ForgeMenu.viewing_armor)
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
            "🔨 **КУЗНЯ**\n\n"
            f"💪 Общая сила: {int(player['strength'])}\n\n"
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
        btn = f"{w_info['emoji']} {w_info['name']} (сила: {w_info['strength']}) — {w_info['cost']} оч."
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

    if player['points'] < new_weapon['cost']:
        await message.answer(
            f"❌ Недостаточно очков!\nТребуется: {new_weapon['cost']}\nУ вас есть: {player['points']}",
            reply_markup=get_next_weapon_kb(current_weapon_id)
        )
        return

    # Купить оружие: сила заменяется, не суммируется
    armor_id = get_player_armor(user_id)
    armor = _get_armor_info(armor_id)
    new_weapon_strength = new_weapon['strength']
    new_total_strength = new_weapon_strength + armor['strength']
    new_points = round(player['points'] - new_weapon['cost'], 1)

    set_player_weapon(user_id, chosen_weapon_id)
    update_player_strength(user_id, new_total_strength)
    update_player_points(user_id, new_points)

    await message.answer(
        f"✅ Оружие улучшено!\n\n"
        f"{new_weapon['emoji']} {new_weapon['name']}\n"
        f"(⚔️) Сила оружия: {new_weapon_strength}\n"
        f"🛡️ Сила брони: {armor['strength']}\n"
        f"(⚔️) Общая сила: {int(new_total_strength)}\n\n"
        f"- {new_weapon['cost']} очков\nОсталось: {new_points}",
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
            "🔨 **КУЗНЯ**\n\n"
            f"💪 Общая сила: {int(player['strength'])}\n\n"
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
        btn = f"{a_info['emoji']} {a_info['name']} (сила: {a_info['strength']}) — {a_info['cost']} оч."
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

    if player['points'] < new_armor['cost']:
        await message.answer(
            f"❌ Недостаточно очков!\nТребуется: {new_armor['cost']}\nУ вас есть: {player['points']}",
            reply_markup=get_next_armor_kb(current_armor_id)
        )
        return

    # Купить броню: сила заменяется, не суммируется
    weapon_id = get_player_weapon(user_id)
    weapon = _get_weapon_info(weapon_id)
    new_armor_strength = new_armor['strength']
    new_total_strength = weapon['strength'] + new_armor_strength
    new_points = round(player['points'] - new_armor['cost'], 1)

    set_player_armor(user_id, chosen_armor_id)
    update_player_strength(user_id, new_total_strength)
    update_player_points(user_id, new_points)

    await message.answer(
        f"✅ Броня улучшена!\n\n"
        f"{new_armor['emoji']} {new_armor['name']}\n"
        f"(⚔️) Сила оружия: {weapon['strength']}\n"
        f"🛡️ Сила брони: {new_armor_strength}\n"
        f"(⚔️) Общая сила: {int(new_total_strength)}\n\n"
        f"- {new_armor['cost']} очков\nОсталось: {new_points}",
        reply_markup=get_next_armor_kb(chosen_armor_id)
    )

# ============== EQUIPMENT SHOP (устарело — кузня заменяет) ==============
@dp.message(F.text == "🎖️ Снаряжение")
async def open_equipment_shop(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    
    equip_text = "🎖️ **МАГАЗИН СНАРЯЖЕНИЯ**\n\n"
    equip_text += f"Твои очки: {player['points']} ⚡\n"
    equip_text += f"Твоя сила: {player['strength']} 💪\n\n"
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
        f"🐉 **РЕЙД — Этаж {floor_id}/10**\n\n"
        f"{enemy_info['emoji']} {enemy_info['name']}\n"
        f"🩶 {enemy_info['health']} HP\n"
        f"⚔️ {enemy_info['base_damage']} атака\n"
        f"💰 Награда: {enemy_info['reward']} очков"
    )

@dp.message(F.text == "🐉 Рейд")
async def open_raid(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)

    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    # Рейд всегда начинается с первого этажа
    floor_id = 1
    update_player_raid_floor(user_id, 1)

    enemy_info = RAID_FLOORS[floor_id]
    player_health = calculate_player_health(player['strength'])
    player_damage = calculate_damage(player['strength'])
    enemy_damage = enemy_info['base_damage']

    raid_text = (
        f"{_get_raid_floor_text(floor_id, enemy_info)}\n\n"
        f"{'═' * 19}\n\n"
        f"👤 {player['nickname']}\n"
        f"❤️ {player_health}\n"
        f"⚔️ {player_damage}\n\n"
        f"Бой начинается!"
    )

    await state.set_state(RaidState.in_raid)
    await state.update_data(
        raid_floor=floor_id,
        player_health=player_health,
        player_damage=player_damage,
        enemy_health=enemy_info['health'],
        enemy_damage=enemy_damage,
    )

    # Определяем, кто ходит первым
    player_goes_first = random.random() < 0.5
    if player_goes_first:
        raid_text += "\n\n🎲 Ты атакуешь первым!\nЧто ты будешь делать?"
        await send_image_with_text(message, "raid.png", raid_text, reply_markup=get_battle_action_kb())
    else:
        await send_image_with_text(message, "raid.png", raid_text + "\n\n🎲 Враг атакует первым...",
                                   reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await asyncio.sleep(2)

        enemy_hit = int(round(enemy_damage * random.uniform(0.7, 1.3)))
        new_player_health = player_health - enemy_hit

        log = (
            f"🐉 **РЕЙД — Этаж {floor_id}/10**\n\n"
            f"{enemy_info['emoji']} {enemy_info['name']} атакует!\n"
            f"💥 Урон: {enemy_hit}\n\n"
        )

        if new_player_health <= 0:
            update_player_raid_floor(user_id, 0)
            log += (f"👤 {player['nickname']} повержен!\n\n❌ **ВЫ ПРОИГРАЛИ!**\n\n"
                    f"Рекорд: {player['raid_max_floor']} этаж.")
            await message.answer(log, reply_markup=get_end_battle_kb())
            await state.clear()
            return

        log += (
            f"{'═' * 19}\n\n"
            f"👤 {player['nickname']}\n❤️ {new_player_health}\n⚔️ {player_damage}\n\n"
            f"{enemy_info['emoji']} {enemy_info['name']}\n🩶 {enemy_info['health']}\n\n"
            "Твой ход!"
        )
        await state.update_data(player_health=new_player_health)
        await message.answer(log, reply_markup=get_battle_action_kb())


@dp.message(RaidState.in_raid)
async def raid_battle_round(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    data = await state.get_data()
    action = message.text

    floor_id = data['raid_floor']
    enemy_info = RAID_FLOORS[floor_id]

    if action not in ("🗡️ Атаковать", "Крит💥20%"):
        if action == "🏠 В главное меню":
            await state.clear()
            await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())
            return
        await message.answer("Выбери действие!", reply_markup=get_battle_action_kb())
        return

    log = f"🐉 **РЕЙД — Этаж {floor_id}/10** ⚔️\n\n"

    if action == "Крит💥20%":
        is_crit = random.random() < 0.20
        if not is_crit:
            # Промах крита — игрок пропускает ход, враг атакует без ответа
            log += f"⚔️ Промах крита! Ход пропущен!\n\n"
            enemy_hit = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
            new_player_health = int(round(data['player_health'] - enemy_hit))
            new_enemy_health = data['enemy_health']
            log += f"{enemy_info['emoji']} {enemy_info['name']} атакует (без ответа)!\n💥 Урон: {enemy_hit}\n\n"
            if new_player_health <= 0:
                floors_completed = floor_id - 1
                new_max = max(player['raid_max_floor'], floors_completed)
                if new_max > player['raid_max_floor']:
                    update_player_raid_max_floor(user_id, new_max)
                update_player_raid_floor(user_id, 0)
                log += (f"👤 {player['nickname']} повержен!\n\n❌ **ВЫ ПРОИГРАЛИ!**\n\n"
                        f"Пройдено этажей: {floors_completed}. Рекорд: {new_max}.")
                await message.answer(log, reply_markup=get_end_battle_kb())
                await state.clear()
                return
            log += (
                f"{'═' * 19}\n\n"
                f"👤 {player['nickname']}\n❤️ {new_player_health}\n⚔️ {data['player_damage']}\n\n"
                f"{enemy_info['emoji']} {enemy_info['name']}\n🩶 {new_enemy_health}\n⚔️ {data['enemy_damage']}\n\n"
                "Что ты будешь делать?"
            )
            await message.answer(log, reply_markup=get_battle_action_kb())
            await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health)
            return
        else:
            # Крит успешный — 2x урон
            base_dmg = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
            player_hit = base_dmg * 2
            log += f"💥 КРИТИЧЕСКИЙ УДАР!\n"
            log += f"👤 {player['nickname']} атакует!\n💥 Урон: {player_hit}\n\n"
    else:
        # Обычная атака
        player_hit = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
        log += f"👤 {player['nickname']} атакует!\n💥 Урон: {player_hit}\n\n"

    new_enemy_health = int(round(data['enemy_health'] - player_hit))

    if new_enemy_health <= 0:
        # Победа на этаже — обновляем рекорд
        reward = enemy_info['reward']
        new_points = round(player['points'] + reward, 1)
        update_player_points(user_id, new_points)
        update_rating_points(user_id, 5)
        if floor_id > player['raid_max_floor']:
            update_player_raid_max_floor(user_id, floor_id)
        player_clan = get_player_clan(user_id)
        clan_exp = 10 if floor_id == 10 else 5
        if player_clan:
            add_clan_exp(player_clan['clan_id'], clan_exp)

        log += f"{enemy_info['emoji']} {enemy_info['name']} повержен!\n\n"
        log += f"✅ **ЭТАЖ {floor_id} ПРОЙДЕН!**\n\n"
        log += f"💰 Награда: +{reward} очков\n"
        log += f"+5💠 очков рейтинга\n"
        if player_clan:
            log += f"+{clan_exp} опыта клану\n"
        log += f"Всего очков: {new_points}\n"

        if floor_id == 10:
            update_player_raid_floor(user_id, 0)
            log += (
                "\n🎉 **ПОЗДРАВЛЯЕМ!**\n"
                "Ты прошёл все 10 этажей рейда!\n"
                "♦️💀 Зеркальный дух повержён!\n\n"
                "Рейд начинается заново с первого этажа."
            )
            await message.answer(log, reply_markup=get_end_battle_kb())
            await state.clear()
        else:
            next_floor = floor_id + 1
            update_player_raid_floor(user_id, next_floor)
            log += f"\n⬆️ Переход на этаж {next_floor}..."
            await message.answer(log, reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
            await asyncio.sleep(2)

            # Автоматически начинаем следующий этаж
            next_enemy = RAID_FLOORS[next_floor]
            player_refreshed = get_player(user_id)
            new_p_health = calculate_player_health(player_refreshed['strength'])
            new_p_damage = calculate_damage(player_refreshed['strength'])

            await state.update_data(
                raid_floor=next_floor,
                player_health=new_p_health,
                player_damage=new_p_damage,
                enemy_health=next_enemy['health'],
                enemy_damage=next_enemy['base_damage'],
            )

            next_text = (
                f"{_get_raid_floor_text(next_floor, next_enemy)}\n\n"
                f"{'═' * 19}\n\n"
                f"👤 {player_refreshed['nickname']}\n"
                f"❤️ {new_p_health}\n"
                f"⚔️ {new_p_damage}\n\n"
                "Твой ход!"
            )
            await message.answer(next_text, reply_markup=get_battle_action_kb())
        return

    # Враг контратакует
    enemy_hit = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
    new_player_health = int(round(data['player_health'] - enemy_hit))

    log += f"{enemy_info['emoji']} {enemy_info['name']} контратакует!\n💥 Урон: {enemy_hit}\n\n"

    if new_player_health <= 0:
        floors_completed = floor_id - 1
        new_max = max(player['raid_max_floor'], floors_completed)
        if new_max > player['raid_max_floor']:
            update_player_raid_max_floor(user_id, new_max)
        update_player_raid_floor(user_id, 0)
        log += (f"👤 {player['nickname']} повержен!\n\n❌ **ВЫ ПРОИГРАЛИ!**\n\n"
                f"Пройдено этажей: {floors_completed}. Рекорд: {new_max}.")
        await message.answer(log, reply_markup=get_end_battle_kb())
        await state.clear()
        return

    log += (
        f"{'═' * 19}\n\n"
        f"👤 {player['nickname']}\n❤️ {new_player_health}\n⚔️ {data['player_damage']}\n\n"
        f"{enemy_info['emoji']} {enemy_info['name']}\n🩶 {new_enemy_health}\n⚔️ {data['enemy_damage']}\n\n"
        "Что ты будешь делать?"
    )
    await message.answer(log, reply_markup=get_battle_action_kb())
    await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health)


# ============== ENEMIES ==============
@dp.message(F.text == "⚔️ Враги")
async def show_enemies(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    
    enemies_text = "⚔️ **ВРАГИ**\n\n"
    
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
    
    # Подготовка боя
    player_health = calculate_player_health(player['strength'])
    player_damage = calculate_damage(player['strength'])
    enemy_info = ENEMIES[selected_enemy]
    enemy_damage = calculate_enemy_damage(selected_enemy)
    
    battle_info = (
        f"⚔️ **ИНФОРМАЦИЯ О БОЕ** ⚔️\n\n"
        f"информация об {player['nickname']}:\n"
        f"❤️ {player_health}\n"
        f"⚔️ {player_damage}\n\n"
        f"☠️ {enemy_info['name']}\n"
        f"🩶 {enemy_info['health']}\n"
        f"⚔️ {enemy_damage}\n"
    )
    
    await message.answer(battle_info, reply_markup=get_battle_kb())
    
    # Сохраняем информацию о бое в FSM
    await state.set_state(BattleState.in_battle)
    await state.update_data(
        selected_enemy=selected_enemy,
        player_health=player_health,
        player_damage=player_damage,
        enemy_health=enemy_info['health'],
        enemy_damage=enemy_damage
    )

@dp.message(BattleState.in_battle, F.text == "⚔️ Начать сражение")
async def start_battle(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    data = await state.get_data()
    selected_enemy = data['selected_enemy']
    enemy_info = ENEMIES[selected_enemy]
    
    # Определяем, кто ходит первым (50% шанс для игрока)
    player_goes_first = random.random() < 0.5
    
    if player_goes_first:
        turn_text = "🎲 Победа в первом ходу! Ты атакуешь первым!\n\n"
        turn_text += f"👤 {player['nickname']}\n❤️ {data['player_health']}\n⚔️ {data['player_damage']}\n\n"
        turn_text += f"☠️ {enemy_info['name']}\n🩶 {data['enemy_health']}\n⚔️ {data['enemy_damage']}\n\n"
        turn_text += "═══════════════════\n"
        turn_text += "Что ты будешь делать?"
        
        await message.answer(turn_text, reply_markup=get_battle_action_kb())
        await state.update_data(player_goes_first=True)
        await state.set_state(BattleState.battle_round)
    else:
        # Враг атакует первый
        await message.answer("🎲 Враг получил инициативу!\n\n☠️ Враг атакует первым...", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await asyncio.sleep(2)
        
        # Враг атакует
        enemy_damage = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
        new_player_health = int(round(data['player_health'] - enemy_damage))
        
        battle_log = f"⚔️ **РАУНД БОЯ** ⚔️\n\n"
        battle_log += f"☠️ {enemy_info['name']} атакует!\n"
        battle_log += f"💥 Урон: {enemy_damage}\n\n"
        
        # Проверяем, жив ли игрок
        if new_player_health <= 0:
            battle_log += f"👤 {player['nickname']} повержен!\n\n"
            battle_log += f"❌ **ВЫ ПРОИГРАЛИ!**\n\n"
            battle_log += f"Ты был повержен {enemy_info['name']}..."
            
            await message.answer(battle_log, reply_markup=get_end_battle_kb())
            await state.clear()
            return
        
        # Продолжаем бой
        battle_log += f"═══════════════════\n\n"
        battle_log += f"👤 {player['nickname']}\n❤️ {new_player_health}\n⚔️ {data['player_damage']}\n\n"
        battle_log += f"☠️ {enemy_info['name']}\n🩶 {data['enemy_health']}\n⚔️ {data['enemy_damage']}\n\n"
        battle_log += f"═══════════════════\n"
        battle_log += "Твой ход!"
        
        await message.answer(battle_log, reply_markup=get_battle_action_kb())
        await state.update_data(player_goes_first=False, player_health=new_player_health)
        await state.set_state(BattleState.battle_round)

@dp.message(BattleState.battle_round)
async def battle_round(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    data = await state.get_data()
    selected_enemy = data['selected_enemy']
    enemy_info = ENEMIES[selected_enemy]
    
    action = message.text
    
    if action == "🗡️ Атаковать":
        # Урон игрока с вариацией
        player_damage = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
        new_enemy_health = int(round(data['enemy_health'] - player_damage))
        
        battle_log = f"⚔️ **РАУНД БОЯ** ⚔️\n\n"
        battle_log += f"👤 {player['nickname']} атакует!\n"
        battle_log += f"💥 Урон: {player_damage}\n\n"
        
        # Проверяем, живого ли врага
        if new_enemy_health <= 0:
            # Победа
            reward = enemy_info['reward']
            new_points = round(player['points'] + reward, 1)
            update_player_points(user_id, new_points)
            update_rating_points(user_id, 5)
            player_clan = get_player_clan(user_id)
            if player_clan:
                add_clan_exp(player_clan['clan_id'], 5)
            
            battle_log += f"☠️ {enemy_info['name']} повержен!\n\n"
            battle_log += f"✅ **ВЫ ПОБЕДИЛИ!**\n\n"
            battle_log += f"💰 Награда: +{reward} очков\n"
            battle_log += f"+5💠 очков рейтинга\n"
            battle_log += f"Всего очков: {new_points}"
            
            await message.answer(battle_log, reply_markup=get_end_battle_kb())
            await state.clear()
            return
        
        # Враг контратакует
        enemy_damage = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
        new_player_health = int(round(data['player_health'] - enemy_damage))
        
        battle_log += f"☠️ {enemy_info['name']} контратакует!\n"
        battle_log += f"💥 Урон: {enemy_damage}\n\n"
        
        # Проверяем, жив ли игрок
        if new_player_health <= 0:
            battle_log += f"👤 {player['nickname']} повержен!\n\n"
            battle_log += f"❌ **ВЫ ПРОИГРАЛИ!**\n\n"
            battle_log += f"Ты был повержен {enemy_info['name']}..."
            
            await message.answer(battle_log, reply_markup=get_end_battle_kb())
            await state.clear()
            return
        
        # Продолжаем бой
        battle_log += f"═══════════════════\n\n"
        battle_log += f"👤 {player['nickname']}\n❤️ {new_player_health}\n⚔️ {data['player_damage']}\n\n"
        battle_log += f"☠️ {enemy_info['name']}\n🩶 {new_enemy_health}\n⚔️ {data['enemy_damage']}\n\n"
        battle_log += f"═══════════════════\n"
        battle_log += "Что ты будешь делать?"
        
        await message.answer(battle_log, reply_markup=get_battle_action_kb())
        await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health)
    
    elif action == "Крит💥20%":
        is_crit = random.random() < 0.20

        if not is_crit:
            # Промах крита — игрок пропускает ход, враг атакует без ответа
            battle_log = f"🗡️ **РАУНД БОЯ** 🗡️\n\n"
            battle_log += f"⚔️ Промах крита! Ход пропущен!\n\n"
            enemy_damage = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
            new_player_health = int(round(data['player_health'] - enemy_damage))
            new_enemy_health = data['enemy_health']
            battle_log += f"☠️ {enemy_info['name']} атакует (без ответа)!\n"
            battle_log += f"💥 Урон: {enemy_damage}\n\n"
            if new_player_health <= 0:
                battle_log += f"👤 {player['nickname']} повержен!\n\n"
                battle_log += f"❌ **ВЫ ПРОИГРАЛИ!**\n\n"
                battle_log += f"Ты был повержен {enemy_info['name']}..."
                await message.answer(battle_log, reply_markup=get_end_battle_kb())
                await state.clear()
                return
            battle_log += f"═══════════════════\n\n"
            battle_log += f"👤 {player['nickname']}\n❤️ {new_player_health}\n⚔️ {data['player_damage']}\n\n"
            battle_log += f"☠️ {enemy_info['name']}\n🩶 {new_enemy_health}\n⚔️ {data['enemy_damage']}\n\n"
            battle_log += f"═══════════════════\n"
            battle_log += "Что ты будешь делать?"
            await message.answer(battle_log, reply_markup=get_battle_action_kb())
            await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health)
            return

        # Крит успешный — 2x урон
        base_damage = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
        player_damage = base_damage * 2
        new_enemy_health = int(round(data['enemy_health'] - player_damage))

        battle_log = f"🗡️ **РАУНД БОЯ** 🗡️\n\n"
        battle_log += f"💥 КРИТИЧЕСКИЙ УДАР!\n"
        battle_log += f"👤 {player['nickname']} атакует!\n"
        battle_log += f"💥 Урон: {player_damage}\n\n"

        if new_enemy_health <= 0:
            reward = enemy_info['reward']
            new_points = round(player['points'] + reward, 1)
            update_player_points(user_id, new_points)
            update_rating_points(user_id, 5)
            player_clan = get_player_clan(user_id)
            if player_clan:
                add_clan_exp(player_clan['clan_id'], 5)
            battle_log += f"☠️ {enemy_info['name']} повержен!\n\n"
            battle_log += f"✅ **ВЫ ПОБЕДИЛИ!**\n\n"
            battle_log += f"💰 Награда: +{reward} очков\n"
            battle_log += f"+5💠 очков рейтинга\n"
            battle_log += f"Всего очков: {new_points}"
            await message.answer(battle_log, reply_markup=get_end_battle_kb())
            await state.clear()
            return

        # Враг контратакует
        enemy_damage = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
        new_player_health = int(round(data['player_health'] - enemy_damage))
        battle_log += f"☠️ {enemy_info['name']} контратакует!\n"
        battle_log += f"💥 Урон: {enemy_damage}\n\n"
        if new_player_health <= 0:
            battle_log += f"👤 {player['nickname']} повержен!\n\n"
            battle_log += f"❌ **ВЫ ПРОИГРАЛИ!**\n\n"
            battle_log += f"Ты был повержен {enemy_info['name']}..."
            await message.answer(battle_log, reply_markup=get_end_battle_kb())
            await state.clear()
            return
        battle_log += f"═══════════════════\n\n"
        battle_log += f"👤 {player['nickname']}\n❤️ {new_player_health}\n⚔️ {data['player_damage']}\n\n"
        battle_log += f"☠️ {enemy_info['name']}\n🩶 {new_enemy_health}\n⚔️ {data['enemy_damage']}\n\n"
        battle_log += f"═══════════════════\n"
        battle_log += "Что ты будешь делать?"
        await message.answer(battle_log, reply_markup=get_battle_action_kb())
        await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health)

@dp.message(BattleState.in_battle, F.text == "❌ Назад")
async def back_to_enemies(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    enemies_text = "⚔️ **ВРАГИ**\n\n"
    
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

    health = calculate_player_health(player['strength'])
    damage = calculate_damage(player['strength'])

    search_text = (
        "🌐 **ОНЛАЙН РЕЖИМ**\n\n"
        f"Твои характеристики:\n"
        f"👤 {player['nickname']}\n"
        f"❤️ {health}\n"
        f"⚔️ {damage}\n"
        f"💪 {int(player['strength'])}🗡️ | {player['wins']}🏆\n\n"
        "🔍 Ищем соперника..."
    )

    pvp_queue[user_id] = {
        "nickname": player['nickname'],
        "strength": player['strength'],
        "wins": player['wins'],
        "health": health,
        "damage": damage,
        "chat_id": message.chat.id
    }

    await send_image_with_text(message, "online.png", search_text, reply_markup=get_searching_kb())
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
            "✅ **СОПЕРНИК НАЙДЕН!**\n\n"
            f"Ваш соперник:\n"
            f"👤 {opponent_data['nickname']}\n"
            f"❤️ {opponent_data['health']}\n"
            f"⚔️ {opponent_data['damage']}\n"
            f"💪 {int(opponent_data['strength'])}🗡️ | {opponent_data['wins']}🏆\n\n"
            "Подтвердите участие!"
        )
        match_text_opp = (
            "✅ **СОПЕРНИК НАЙДЕН!**\n\n"
            f"Ваш соперник:\n"
            f"👤 {my_data['nickname']}\n"
            f"❤️ {my_data['health']}\n"
            f"⚔️ {my_data['damage']}\n"
            f"💪 {int(my_data['strength'])}🗡️ | {my_data['wins']}🏆\n\n"
            "Подтвердите участие!"
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
            reply_markup=get_pvp_accept_kb()
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

            # Для текущего игрока
            await state.update_data(
                pvp_player_health=data['my_health'],
                pvp_player_damage=data['my_damage'],
                pvp_enemy_health=data['opp_health'],
                pvp_enemy_damage=data['opp_damage'],
                pvp_goes_first=player_goes_first,
                pvp_my_turn=player_goes_first
            )
            await state.set_state(OnlineState.in_pvp_battle)

            # Для оппонента (ход противоположный)
            await opp_state.update_data(
                pvp_player_health=opp_data['my_health'],
                pvp_player_damage=opp_data['my_damage'],
                pvp_enemy_health=opp_data['opp_health'],
                pvp_enemy_damage=opp_data['opp_damage'],
                pvp_goes_first=not player_goes_first,
                pvp_my_turn=not player_goes_first
            )
            await opp_state.set_state(OnlineState.in_pvp_battle)

            opp_player = get_player(opponent_id)
            my_player = get_player(user_id)

            first_name = my_player['nickname'] if player_goes_first else opp_player['nickname']
            start_text = f"⚔️ **БОЙ НАЧАЛСЯ!**\n\nПервым ходит: {first_name}\n"

            if player_goes_first:
                await message.answer(
                    start_text + "\n🗡️ Твой ход!",
                    reply_markup=get_battle_action_kb()
                )
                await bot.send_message(
                    chat_id=opponent_id,
                    text=start_text + "\n⏳ Ход соперника...",
                    reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
                )
            else:
                await message.answer(
                    start_text + "\n⏳ Ход соперника...",
                    reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
                )
                await bot.send_message(
                    chat_id=opponent_id,
                    text=start_text + "\n🗡️ Твой ход!",
                    reply_markup=get_battle_action_kb()
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

    my_health = data['pvp_player_health']
    my_damage = data['pvp_player_damage']
    enemy_health = data['pvp_enemy_health']
    enemy_damage = data['pvp_enemy_damage']

    if text == "🗡️ Атаковать":
        dealt = int(round(my_damage * random.uniform(0.8, 1.2)))
        new_enemy_health = int(round(enemy_health - dealt))

        battle_log = f"⚔️ **PvP БОЙ** ⚔️\n\nТы атакуешь!\n💥 Урон: {dealt}\n\n"

        if new_enemy_health <= 0:
            update_player_wins(user_id)
            update_rating_points(user_id, 7)
            winner_clan = get_player_clan(user_id)
            if winner_clan:
                add_clan_exp(winner_clan['clan_id'], 1)
            battle_log += "✅ **ВЫ ПОБЕДИЛИ!**\n(+1 победа, +7💠 рейтинга)"
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
                        text=f"⚔️ **PvP БОЙ** ⚔️\n\nСоперник атакует!\n💥 Урон: {dealt}\n\n❌ **ВЫ ПРОИГРАЛИ!**",
                        reply_markup=get_end_battle_kb()
                    )
                except Exception:
                    pass
            return

        # Передаём ход сопернику
        battle_log += (
            f"👤 Ты: ❤️ {my_health}\n"
            f"👤 Соперник: ❤️ {new_enemy_health}\n\n"
            "⏳ Ход соперника..."
        )
        await message.answer(battle_log, reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        # Обновляем здоровье противника в своём стейте
        await state.update_data(pvp_enemy_health=new_enemy_health, pvp_my_turn=False)

        if opponent_id:
            opp_state = dp.fsm.resolve_context(bot, opponent_id, opponent_id)
            opp_data = await opp_state.get_data()
            # У соперника pvp_player_health = это моё здоровье (для них мы — противник)
            # Они атаковали нас — значит их pvp_enemy_health уменьшилось
            # Нет, они НЕ атаковали — это МЫ атаковали ИХ.
            # С точки зрения соперника: их pvp_enemy_health (= наше здоровье) не менялось,
            # а их pvp_player_health (= их здоровье) уменьшилось на dealt.
            new_opp_player_health = int(round(opp_data.get('pvp_player_health', 0) - dealt))
            await opp_state.update_data(
                pvp_player_health=new_opp_player_health,
                pvp_my_turn=True
            )
            try:
                await bot.send_message(
                    chat_id=opponent_id,
                    text=(
                        f"⚔️ **PvP БОЙ** ⚔️\n\n"
                        f"Соперник атакует! 💥 {dealt} урона\n\n"
                        f"👤 Ты: ❤️ {new_opp_player_health}\n"
                        f"👤 Соперник: ❤️ {opp_data.get('pvp_enemy_health', 0)}\n\n"
                        "🗡️ Твой ход!"
                    ),
                    reply_markup=get_battle_action_kb()
                )
            except Exception:
                pass

    elif text == "Крит💥20%":
        is_crit = random.random() < 0.20

        if not is_crit:
            # Промах крита в PvP — ход пропущен (0 урона), передаём ход сопернику
            battle_log = f"⚔️ **PvP БОЙ** ⚔️\n\n⚔️ Промах крита! Ход пропущен!\n\n"
            battle_log += (
                f"👤 Ты: ❤️ {my_health}\n"
                f"👤 Соперник: ❤️ {enemy_health}\n\n"
                "⏳ Ход соперника..."
            )
            await message.answer(battle_log, reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
            await state.update_data(pvp_my_turn=False)
            if opponent_id:
                opp_state = dp.fsm.resolve_context(bot, opponent_id, opponent_id)
                await opp_state.update_data(pvp_my_turn=True)
                try:
                    await bot.send_message(
                        chat_id=opponent_id,
                        text=(
                            f"⚔️ **PvP БОЙ** ⚔️\n\n"
                            f"Соперник промахнулся по криту! Его ход пропущен.\n\n"
                            "🗡️ Твой ход!"
                        ),
                        reply_markup=get_battle_action_kb()
                    )
                except Exception:
                    pass
            return

        # Крит успешный — 2x урон
        base_dealt = int(round(my_damage * random.uniform(0.8, 1.2)))
        dealt = base_dealt * 2
        new_enemy_health = int(round(enemy_health - dealt))

        battle_log = f"⚔️ **PvP БОЙ** ⚔️\n\n💥 КРИТИЧЕСКИЙ УДАР!\nТы атакуешь!\n💥 Урон: {dealt}\n\n"

        if new_enemy_health <= 0:
            update_player_wins(user_id)
            update_rating_points(user_id, 7)
            winner_clan = get_player_clan(user_id)
            if winner_clan:
                add_clan_exp(winner_clan['clan_id'], 1)
            battle_log += "✅ **ВЫ ПОБЕДИЛИ!**\n(+1 победа, +7💠 рейтинга)"
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
                        text=f"⚔️ **PvP БОЙ** ⚔️\n\nСоперник атакует!\n💥 Урон: {dealt}\n\n❌ **ВЫ ПРОИГРАЛИ!**",
                        reply_markup=get_end_battle_kb()
                    )
                except Exception:
                    pass
            return

        # Передаём ход сопернику
        battle_log += (
            f"👤 Ты: ❤️ {my_health}\n"
            f"👤 Соперник: ❤️ {new_enemy_health}\n\n"
            "⏳ Ход соперника..."
        )
        await message.answer(battle_log, reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.update_data(pvp_enemy_health=new_enemy_health, pvp_my_turn=False)

        if opponent_id:
            opp_state = dp.fsm.resolve_context(bot, opponent_id, opponent_id)
            opp_data = await opp_state.get_data()
            new_opp_player_health = int(round(opp_data.get('pvp_player_health', 0) - dealt))
            await opp_state.update_data(
                pvp_player_health=new_opp_player_health,
                pvp_my_turn=True
            )
            try:
                await bot.send_message(
                    chat_id=opponent_id,
                    text=(
                        f"⚔️ **PvP БОЙ** ⚔️\n\n"
                        f"Соперник атакует! 💥 {dealt} урона\n\n"
                        f"👤 Ты: ❤️ {new_opp_player_health}\n"
                        f"👤 Соперник: ❤️ {opp_data.get('pvp_enemy_health', 0)}\n\n"
                        "🗡️ Твой ход!"
                    ),
                    reply_markup=get_battle_action_kb()
                )
            except Exception:
                pass
    else:
        await message.answer("Выбери действие!", reply_markup=get_battle_action_kb())

# ============== CLANS ==============
def _format_clan_menu(clan: dict, leader_nickname: str) -> str:
    """Форматировать текст меню клана"""
    if clan['clan_level'] >= MAX_CLAN_LEVEL:
        exp_display = f"{clan['clan_exp']}📈 (МАКС 🧬)"
    else:
        max_exp = CLAN_LEVEL_EXP[clan['clan_level']]
        exp_display = f"{clan['clan_exp']} / {max_exp}📈"
    return (
        f"[🛡️] Клан: {clan['clan_name']}\n"
        f"[👑] Глава: {leader_nickname}\n"
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
        await send_image_with_text(message, "myclan.png", clan_text, reply_markup=get_my_clan_kb(is_leader))
        await state.set_state(ClanMenu.viewing_my_clan)
        await state.update_data(clan_id=my_clan['clan_id'])
    else:
        clans = get_all_clans()
        if clans:
            clans_text = "🛡️ **СПИСОК КЛАНОВ**\n\n"
            for clan in clans:
                _, name, lvl, members, min_power, ldr = clan
                clans_text += f"🛡️ {name} — ур.{lvl} | {members}👥 | порог: {min_power}⚔️\n"
        else:
            clans_text = "🛡️ **КЛАНОВ ЕЩЁ НЕТ**\n\nСтань первым!"
        await send_image_with_text(message, "clan.png", clans_text, reply_markup=get_clans_list_kb(clans))
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
        if player['points'] < 2000:
            await message.answer(
                f"❌ Недостаточно очков!\nТребуется: 2000🔸\nУ вас: {player['points']}🔸",
                reply_markup=get_clans_list_kb(get_all_clans())
            )
            return
        await message.answer(
            "Вы хотите потратить 2000🔸 очков на создание клана?",
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
        if player['points'] < 2000:
            await message.answer("❌ Недостаточно очков для создания клана!", reply_markup=get_main_kb())
            await state.clear()
            return
        update_player_points(user_id, round(player['points'] - 2000, 1))
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

    if text == "🚪 Выйти из клана" and not is_leader:
        leave_clan(user_id, clan_id)
        await state.clear()
        clans = get_all_clans()
        await message.answer("Вы вышли из клана.", reply_markup=get_clans_list_kb(clans))
        await state.set_state(ClanMenu.viewing_clans)
        return

    if text == "👢 Кикнуть игрока" and is_leader:
        members = get_clan_members(clan_id)
        non_leaders = [(uid, nick, st) for uid, nick, st in members if uid != clan['leader_id']]
        if not non_leaders:
            await message.answer("В клане нет участников для кика.", reply_markup=get_my_clan_kb(True))
            return
        await message.answer("Выберите игрока для кика:", reply_markup=get_kick_members_kb(members, clan['leader_id']))
        await state.set_state(ClanMenu.kicking_member)
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

    # Обновить и показать информацию о клане
    leader = get_player(clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(clan, leader_name)
    await message.answer(clan_text, reply_markup=get_my_clan_kb(is_leader))

@dp.message(ClanMenu.kicking_member)
async def handle_kick_member(message: types.Message, state: FSMContext):
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

    # Найти участника по нику
    members = get_clan_members(clan_id)
    kicked = False
    for member_id, nickname, strength in members:
        if member_id != clan['leader_id'] and text == f"👤 {nickname}":
            kick_clan_member(member_id, clan_id)
            kicked = True
            await message.answer(f"✅ Игрок {nickname} исключён из клана.")
            break

    if not kicked:
        await message.answer("❌ Игрок не найден!", reply_markup=get_kick_members_kb(members, clan['leader_id']))
        return

    updated_clan = get_clan(clan_id)
    leader = get_player(updated_clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(updated_clan, leader_name)
    await message.answer(clan_text, reply_markup=get_my_clan_kb(True))
    await state.set_state(ClanMenu.viewing_my_clan)

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

# ============== ADMIN PANEL ==============
@dp.message(Command("adminpanel672030"))
async def open_admin_panel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
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
    if text == "⚡️ Накрутить мощь клика":
        await message.answer("Введите никнейм игрока:",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(AdminPanel.adding_click_power_nickname)
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
    await message.answer("Введите сумму очков для добавления:")
    await state.set_state(AdminPanel.adding_coins_amount)

@dp.message(AdminPanel.adding_coins_amount)
async def admin_coins_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректное число:")
        return
    data = await state.get_data()
    add_points_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount}🔸 добавлено игроку {data['target_nickname']}")
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

@dp.message(AdminPanel.adding_click_power_nickname)
async def admin_click_power_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"❌ Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите сумму мощи клика для добавления:")
    await state.set_state(AdminPanel.adding_click_power_amount)

@dp.message(AdminPanel.adding_click_power_amount)
async def admin_click_power_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректное число:")
        return
    data = await state.get_data()
    add_click_power_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount} мощи клика добавлено игроку {data['target_nickname']}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

# ============== MAIN ==============
async def main():
    init_database()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")

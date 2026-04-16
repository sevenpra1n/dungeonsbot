import sqlite3
import random
import logging
from datetime import datetime, timezone
from bot.config import DB_NAME

# ============== DATA CONSTANTS ==============
# These data constants are here temporarily; they will be imported from bot.data modules later.

EXPERIENCE_LEVELS = {
    1: 0, 2: 100, 3: 250, 4: 500, 5: 950,
    6: 1250, 7: 1800, 8: 2200, 9: 3000, 10: 4500,
    11: 7500, 12: 11500, 13: 14000, 14: 19000, 15: 25000,
    16: 32000, 17: 50000, 18: 80000, 19: 120000, 20: 200000,
}
MAX_PLAYER_LEVEL = 20

STATUSES = {
    1: {"name": "Новичок",      "emoji": "🔸", "custom_emoji": '<tg-emoji emoji-id="5323718538710491847">🔸</tg-emoji>', "required_level": 1,  "type": "default"},
    2: {"name": "Продвинутый",  "emoji": "🌱", "custom_emoji": '<tg-emoji emoji-id="5343920308229256142">🌱</tg-emoji>', "required_level": 5,  "type": "unlock_level"},
    3: {"name": "Охотник",      "emoji": "🔪", "custom_emoji": '<tg-emoji emoji-id="5224460534534916102">🔪</tg-emoji>', "required_level": 1,  "type": "free"},
    4: {"name": "Любитель PVP", "emoji": "⚔️", "custom_emoji": '<tg-emoji emoji-id="5454014806950429357">⚔️</tg-emoji>', "required_level": 1,  "type": "free"},
    5: {"name": "Добытчик",     "emoji": "🥇", "custom_emoji": '<tg-emoji emoji-id="6278187557532472415">🥇</tg-emoji>', "required_level": 1,  "type": "free"},
    # Page 2 - new statuses
    6:  {"name": "Сердцеед",     "emoji": "❤️", "custom_emoji": '<tg-emoji emoji-id="5355174247826217637">❤️</tg-emoji>', "required_level": 1, "type": "unlock_friends", "required_friends": 1},
    7:  {"name": "Стиляга",      "emoji": "👓", "custom_emoji": '<tg-emoji emoji-id="5834901642155137299">👓</tg-emoji>', "required_level": 1, "type": "unlock_strength", "required_strength": 200},
    8:  {"name": "Press F",      "emoji": "⚰️", "custom_emoji": '<tg-emoji emoji-id="5938394329465756346">🎁</tg-emoji>', "required_level": 1, "type": "unlock_deaths", "required_deaths": 20},
    9:  {"name": "Лидер",        "emoji": "👑", "custom_emoji": '<tg-emoji emoji-id="5936238625250350064">🎁</tg-emoji>', "required_level": 1, "type": "unlock_strength", "required_strength": 1000},
    10: {"name": "Удачливый",    "emoji": "🍀", "custom_emoji": '<tg-emoji emoji-id="5960593366151337910">🎁</tg-emoji>', "required_level": 1, "type": "unlock_dodges", "required_dodges": 30},
    # Page 3 - new statuses
    11: {"name": "Гладиатор",    "emoji": "🏛", "custom_emoji": '<tg-emoji emoji-id="6001349144046737619">🎁</tg-emoji>', "required_level": 1, "type": "unlock_pve_wins", "required_pve_wins": 50},
    12: {"name": "Убийца",       "emoji": "👹", "custom_emoji": '<tg-emoji emoji-id="5796297917752941521">👹</tg-emoji>', "required_level": 1, "type": "unlock_pve_wins", "required_pve_wins": 120},
    13: {"name": "Творчество",   "emoji": "🎨", "custom_emoji": '<tg-emoji emoji-id="6021462012037437193">🎁</tg-emoji>', "required_level": 1, "type": "unlock_clan_image"},
    14: {"name": "Пример для подражания", "emoji": "🌠", "custom_emoji": '<tg-emoji emoji-id="6021486768228940485">🎁</tg-emoji>', "required_level": 1, "type": "unlock_strength", "required_strength": 2000},
    15: {"name": "Какашка",      "emoji": "💩", "custom_emoji": '<tg-emoji emoji-id="6005662304824203821">💩</tg-emoji>', "required_level": 1, "type": "unlock_spam"},
    16: {"name": "багоюзер 777", "emoji": "💎", "custom_emoji": '<tg-emoji emoji-id="5354902509540370798">💎</tg-emoji>', "required_level": 1, "type": "unlock_bagouser"},
    # Page 4 - chest statuses
    17: {"name": "Руинер",                "emoji": "💣", "custom_emoji": '<tg-emoji emoji-id="5886484710481205789">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    18: {"name": "Хакер",                 "emoji": "💻", "custom_emoji": '<tg-emoji emoji-id="6021412890496473421">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    19: {"name": "Щедрый",                "emoji": "🤲", "custom_emoji": '<tg-emoji emoji-id="6001349144046737619">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    20: {"name": "Шахтер",                "emoji": "⛏️", "custom_emoji": '<tg-emoji emoji-id="5456456455634370613">⛏️</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    21: {"name": "Очаровашка",            "emoji": "✨", "custom_emoji": '<tg-emoji emoji-id="5938394329465756346">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    22: {"name": "Доверие",               "emoji": "🤝", "custom_emoji": '<tg-emoji emoji-id="6021462012037437193">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    23: {"name": "На богатом",            "emoji": "💰", "custom_emoji": '<tg-emoji emoji-id="6021486768228940485">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    24: {"name": "Лучший в своем деле",   "emoji": "🏆", "custom_emoji": '<tg-emoji emoji-id="5312315739842026755">🏆</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    25: {"name": "Дизайнер",              "emoji": "🎨", "custom_emoji": '<tg-emoji emoji-id="5222021318378948590">🎨</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
}

# Allowed inventory material column names (validated before use in SQL)
ALLOWED_INVENTORY_MATERIALS = frozenset({
    'food', 'wood', 'stone', 'iron', 'gold',
    'copper', 'steel', 'amethyst', 'gem',
    'chest_wood', 'chest_steel', 'chest_gold', 'chest_divine',
})

CLAN_LEVEL_EXP = {1: 100, 2: 250, 3: 500, 4: 950, 5: 1500}
MAX_CLAN_LEVEL = 5

BOSS_HEALTH_MULTIPLIER = 0.9   # Здоровье босса = сила * BOSS_HEALTH_MULTIPLIER
MAX_CLAN_BOSS_TICKETS = 3       # Максимум билетов кланового босса на игрока

CLAN_BOSSES_CONFIG = {
    1: {
        "name": "Подземельный мастер",
        "strength": 75000,
        "health": int(75000 * BOSS_HEALTH_MULTIPLIER),   # 67500
        "damage": 175,
        "rewards": {
            "crystals_base": 10,
            "crystals_bonus": 5,
            "crystals_bonus_chance": 0.20,
            "coins_by_strength": [(200, 1200), (800, 2500), (None, 8500)],
            "exp_profile": (220, 300),
            "exp_clan": 120,
            "rating": 50,
        },
        "cooldown_minutes": 30,
    },
    2: {
        "name": "Заклятый дух клана",
        "strength": 290000,
        "health": int(290000 * BOSS_HEALTH_MULTIPLIER),  # 261000
        "damage": 460,
        "rewards": {
            "crystals_base": 50,
            "crystals_bonus": 100,
            "crystals_bonus_chance": 0.20,
            "coins_by_strength": [(200, 5600), (800, 8900), (None, 15000)],
            "exp_profile": (1250, 1250),
            "exp_clan": 450,
            "rating": 100,
        },
        "cooldown_minutes": 30,
    },
}

CLAN_BUFFS = {
    1: {"power_pct": 0.0,  "click_bonus": 0},
    2: {"power_pct": 0.05, "click_bonus": 5},
    3: {"power_pct": 0.10, "click_bonus": 30},
    4: {"power_pct": 0.30, "click_bonus": 100},
    5: {"power_pct": 0.60, "click_bonus": 250},
}

# Emoji constant used by get_rating_league
E_GIFT     = '<tg-emoji emoji-id="5429203678529613915">🎁</tg-emoji>'


# ============== DATABASE INIT ==============

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
        'ALTER TABLE players ADD COLUMN deaths INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN dodges INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN pve_wins INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN has_set_clan_image INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN is_spammer INTEGER DEFAULT 0',
        'ALTER TABLE players ADD COLUMN likes INTEGER DEFAULT 0',
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
    # Миграция: добавить новые колонки материалов если их нет
    for inv_col in [
        'ALTER TABLE player_inventory ADD COLUMN copper INTEGER DEFAULT 0',
        'ALTER TABLE player_inventory ADD COLUMN steel INTEGER DEFAULT 0',
        'ALTER TABLE player_inventory ADD COLUMN amethyst INTEGER DEFAULT 0',
        'ALTER TABLE player_inventory ADD COLUMN gem INTEGER DEFAULT 0',
        'ALTER TABLE player_inventory ADD COLUMN chest_wood INTEGER DEFAULT 0',
        'ALTER TABLE player_inventory ADD COLUMN chest_steel INTEGER DEFAULT 0',
        'ALTER TABLE player_inventory ADD COLUMN chest_gold INTEGER DEFAULT 0',
        'ALTER TABLE player_inventory ADD COLUMN chest_divine INTEGER DEFAULT 0',
    ]:
        try:
            cursor.execute(inv_col)
            conn.commit()
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logging.warning(f"Inventory migration warning: {e}")

    # Таблица компонентов игрока
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_components (
            user_id INTEGER PRIMARY KEY,
            common INTEGER DEFAULT 0,
            rare INTEGER DEFAULT 0,
            epic INTEGER DEFAULT 0,
            legendary INTEGER DEFAULT 0,
            mythic INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO player_components (user_id)
        SELECT user_id FROM players
    ''')
    # Миграция: добавить колонки компонентов если их нет (для старых БД)
    for comp_col in [
        'ALTER TABLE player_components ADD COLUMN common INTEGER DEFAULT 0',
        'ALTER TABLE player_components ADD COLUMN rare INTEGER DEFAULT 0',
        'ALTER TABLE player_components ADD COLUMN epic INTEGER DEFAULT 0',
        'ALTER TABLE player_components ADD COLUMN legendary INTEGER DEFAULT 0',
        'ALTER TABLE player_components ADD COLUMN mythic INTEGER DEFAULT 0',
    ]:
        try:
            cursor.execute(comp_col)
            conn.commit()
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logging.warning(f"Components migration warning: {e}")

    # Таблица разблокированных сундучных статусов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_chest_statuses (
            user_id INTEGER NOT NULL,
            status_name TEXT NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, status_name),
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

    # Таблица купленных топоров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_axes (
            user_id INTEGER PRIMARY KEY,
            axe_level INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES players(user_id)
        )
    ''')

    # Создать записи инвентаря для существующих игроков
    cursor.execute('''
        INSERT OR IGNORE INTO player_inventory (user_id)
        SELECT user_id FROM players
    ''')

    # Таблица дружбы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friendships (
            user_id INTEGER NOT NULL,
            friend_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, friend_id),
            FOREIGN KEY (user_id) REFERENCES players(user_id),
            FOREIGN KEY (friend_id) REFERENCES players(user_id)
        )
    ''')

    # Таблица кланового босса
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clan_bosses (
            clan_id INTEGER PRIMARY KEY,
            boss_num INTEGER DEFAULT 1,
            current_health INTEGER DEFAULT 0,
            last_defeated_at TIMESTAMP DEFAULT NULL,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'cooldown')),
            FOREIGN KEY (clan_id) REFERENCES clans(clan_id)
        )
    ''')

    # Таблица билетов кланового босса
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clan_boss_tickets (
            user_id INTEGER NOT NULL,
            clan_id INTEGER NOT NULL,
            tickets INTEGER DEFAULT 3,
            last_refresh TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, clan_id),
            FOREIGN KEY (user_id) REFERENCES players(user_id),
            FOREIGN KEY (clan_id) REFERENCES clans(clan_id)
        )
    ''')

    # Таблица урона кланового босса (для отслеживания кто участвовал)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clan_boss_damage (
            user_id INTEGER NOT NULL,
            clan_id INTEGER NOT NULL,
            total_damage INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, clan_id),
            FOREIGN KEY (user_id) REFERENCES players(user_id),
            FOREIGN KEY (clan_id) REFERENCES clans(clan_id)
        )
    ''')

    # Таблица лайков профиля (один лайк от одного игрока другому)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_likes (
            liker_id INTEGER NOT NULL,
            liked_id INTEGER NOT NULL,
            message TEXT DEFAULT '',
            PRIMARY KEY (liker_id, liked_id),
            FOREIGN KEY (liker_id) REFERENCES players(user_id),
            FOREIGN KEY (liked_id) REFERENCES players(user_id)
        )
    ''')
    # Migration: add message column if missing
    try:
        cursor.execute("ALTER TABLE player_likes ADD COLUMN message TEXT DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            logging.warning(f"Migration warning: {e}")

    conn.commit()
    conn.close()


# ============== PLAYER MANAGEMENT ==============

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
               COALESCE(online_matches, 0),
               COALESCE(deaths, 0), COALESCE(dodges, 0), COALESCE(pve_wins, 0),
               COALESCE(has_set_clan_image, 0), COALESCE(is_spammer, 0),
               COALESCE(likes, 0)
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
            "deaths": result[18],
            "dodges": result[19],
            "pve_wins": result[20],
            "has_set_clan_image": result[21],
            "is_spammer": result[22],
            "likes": result[23],
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

def get_player_status_emoji(player: dict) -> str:
    """Вернуть кастомный HTML эмодзи статуса игрока"""
    status_name = player.get('status', 'Новичок')
    for s in STATUSES.values():
        if s['name'] == status_name:
            return s.get('custom_emoji', s['emoji'])
    return '🔸'

def set_player_status(user_id: int, status_name: str):
    """Установить статус игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE players SET status = ? WHERE user_id = ?', (status_name, user_id))
    conn.commit()
    conn.close()


# ============== FRIENDSHIP FUNCTIONS ==============

def send_friend_request(user_id: int, friend_id: int) -> str:
    """Отправить заявку в друзья. Возвращает: 'sent', 'already_friends', 'already_pending', 'self'"""
    if user_id == friend_id:
        return 'self'
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Check if already friends or pending
    cursor.execute('''
        SELECT status FROM friendships
        WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)
    ''', (user_id, friend_id, friend_id, user_id))
    row = cursor.fetchone()
    if row:
        conn.close()
        if row[0] == 'accepted':
            return 'already_friends'
        return 'already_pending'
    cursor.execute('''
        INSERT INTO friendships (user_id, friend_id, status) VALUES (?, ?, 'pending')
    ''', (user_id, friend_id))
    conn.commit()
    conn.close()
    return 'sent'

def accept_friend_request(user_id: int, requester_id: int) -> bool:
    """Принять заявку в друзья. user_id - тот кто принимает, requester_id - тот кто отправил."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE friendships SET status = 'accepted'
        WHERE user_id = ? AND friend_id = ? AND status = 'pending'
    ''', (requester_id, user_id))
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def decline_friend_request(user_id: int, requester_id: int) -> bool:
    """Отклонить заявку в друзья."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM friendships
        WHERE user_id = ? AND friend_id = ? AND status = 'pending'
    ''', (requester_id, user_id))
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def remove_friend(user_id: int, friend_id: int) -> bool:
    """Удалить друга (удаляет связь в обе стороны)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM friendships
        WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)
    ''', (user_id, friend_id, friend_id, user_id))
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def get_friends_list(user_id: int) -> list:
    """Получить список друзей (accepted). Возвращает list of user_ids."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT CASE WHEN user_id = ? THEN friend_id ELSE user_id END as fid
        FROM friendships
        WHERE (user_id = ? OR friend_id = ?) AND status = 'accepted'
    ''', (user_id, user_id, user_id))
    friends = [row[0] for row in cursor.fetchall()]
    conn.close()
    return friends

def get_friend_requests(user_id: int) -> list:
    """Получить входящие заявки в друзья (pending). Возвращает list of user_ids."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id FROM friendships
        WHERE friend_id = ? AND status = 'pending'
    ''', (user_id,))
    requests = [row[0] for row in cursor.fetchall()]
    conn.close()
    return requests

def get_friends_count(user_id: int) -> int:
    """Количество друзей (accepted)."""
    return len(get_friends_list(user_id))

def get_friendship_status(user_id: int, other_id: int) -> str:
    """Статус дружбы: 'none', 'pending_sent', 'pending_received', 'accepted'"""
    if user_id == other_id:
        return 'self'
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, friend_id, status FROM friendships
        WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)
    ''', (user_id, other_id, other_id, user_id))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return 'none'
    if row[2] == 'accepted':
        return 'accepted'
    if row[0] == user_id:
        return 'pending_sent'
    return 'pending_received'

def increment_player_deaths(user_id: int):
    """Увеличить счётчик смертей на 1"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE players SET deaths = COALESCE(deaths, 0) + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def increment_player_dodges(user_id: int):
    """Увеличить счётчик уворотов/промахов на 1"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE players SET dodges = COALESCE(dodges, 0) + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def increment_player_pve_wins(user_id: int):
    """Увеличить счётчик PvE побед (локации/рейд) на 1"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE players SET pve_wins = COALESCE(pve_wins, 0) + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def has_liked_player(liker_id: int, liked_id: int) -> bool:
    """Проверить, поставил ли liker_id лайк игроку liked_id"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM player_likes WHERE liker_id = ? AND liked_id = ?', (liker_id, liked_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def give_like_to_player(liker_id: int, liked_id: int, message: str = '') -> bool:
    """Поставить лайк с посланием. Возвращает True если лайк добавлен, False если уже лайкал или сам себе."""
    if liker_id == liked_id:
        return False
    if has_liked_player(liker_id, liked_id):
        return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO player_likes (liker_id, liked_id, message) VALUES (?, ?, ?)', (liker_id, liked_id, message))
    cursor.execute('UPDATE players SET likes = COALESCE(likes, 0) + 1 WHERE user_id = ?', (liked_id,))
    conn.commit()
    conn.close()
    return True

def set_player_clan_image_flag(user_id: int):
    """Отметить что игрок установил картину в клане"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE players SET has_set_clan_image = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def set_player_spammer_flag(user_id: int):
    """Отметить что игрок наспамил в чате клана"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE players SET is_spammer = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


# ============== INVENTORY FUNCTIONS ==============

def get_inventory(user_id: int) -> dict:
    """Получить инвентарь игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT food, wood, stone, iron, gold, '
        'COALESCE(copper,0), COALESCE(steel,0), COALESCE(amethyst,0), COALESCE(gem,0), '
        'COALESCE(chest_wood,0), COALESCE(chest_steel,0), COALESCE(chest_gold,0), COALESCE(chest_divine,0) '
        'FROM player_inventory WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'food': row[0], 'wood': row[1], 'stone': row[2], 'iron': row[3], 'gold': row[4],
            'copper': row[5], 'steel': row[6], 'amethyst': row[7], 'gem': row[8],
            'chest_wood': row[9], 'chest_steel': row[10], 'chest_gold': row[11], 'chest_divine': row[12],
        }
    return {'food': 0, 'wood': 0, 'stone': 0, 'iron': 0, 'gold': 0,
            'copper': 0, 'steel': 0, 'amethyst': 0, 'gem': 0,
            'chest_wood': 0, 'chest_steel': 0, 'chest_gold': 0, 'chest_divine': 0}

def add_inventory_material(user_id: int, material: str, amount: int):
    """Добавить материал в инвентарь"""
    if material not in ALLOWED_INVENTORY_MATERIALS:
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

def remove_inventory_material(user_id: int, material: str, amount: int) -> bool:
    """Снять материал из инвентаря. Возвращает True если успешно."""
    if material not in ALLOWED_INVENTORY_MATERIALS:
        return False
    inv = get_inventory(user_id)
    if inv.get(material, 0) < amount:
        return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        f'UPDATE player_inventory SET {material} = MAX(0, COALESCE({material}, 0) - ?) WHERE user_id = ?',
        (amount, user_id)
    )
    conn.commit()
    conn.close()
    return True


def get_components(user_id: int) -> dict:
    """Получить компоненты игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT COALESCE(common,0), COALESCE(rare,0), COALESCE(epic,0), '
        'COALESCE(legendary,0), COALESCE(mythic,0) '
        'FROM player_components WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'common': row[0], 'rare': row[1], 'epic': row[2], 'legendary': row[3], 'mythic': row[4]}
    return {'common': 0, 'rare': 0, 'epic': 0, 'legendary': 0, 'mythic': 0}

def add_component(user_id: int, rarity: str, amount: int = 1):
    """Добавить компонент нужной редкости"""
    allowed = {'common', 'rare', 'epic', 'legendary', 'mythic'}
    if rarity not in allowed:
        return
    # Map rarity to column index to avoid f-string SQL
    col_map = {'common': 'common', 'rare': 'rare', 'epic': 'epic', 'legendary': 'legendary', 'mythic': 'mythic'}
    col = col_map[rarity]
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO player_components (user_id) VALUES (?)', (user_id,))
    # Column name is validated against a known-safe set above
    cursor.execute(f'UPDATE player_components SET {col} = COALESCE({col}, 0) + ? WHERE user_id = ?',
                   (amount, user_id))
    conn.commit()
    conn.close()


def get_unlocked_chest_statuses(user_id: int) -> set:
    """Получить множество названий разблокированных сундучных статусов игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT status_name FROM player_chest_statuses WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}

def unlock_chest_status(user_id: int, status_name: str):
    """Разблокировать сундучный статус (если ещё не разблокирован)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO player_chest_statuses (user_id, status_name) VALUES (?, ?)',
                   (user_id, status_name))
    conn.commit()
    conn.close()


def get_player_with_chest_statuses(user_id: int) -> dict | None:
    """Получить данные игрока с флагами разблокированных сундучных статусов"""
    player = get_player(user_id)
    if not player:
        return None
    unlocked = get_unlocked_chest_statuses(user_id)
    for status_info in STATUSES.values():
        if status_info.get('type') == 'unlock_chest':
            key = '_chest_unlocked_' + status_info['name']
            player[key] = status_info['name'] in unlocked
    return player


# ============== ACTIVITY FUNCTIONS ==============

def start_activity(user_id: int, activity_type: str, location_id: int, duration_seconds: int):
    """Начать активность в локации"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now(timezone.utc)
    end = datetime.now(timezone.utc).replace(microsecond=0)
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
    now = datetime.now(timezone.utc)
    if now >= end_time:
        return activity
    return None


# ============== EQUIPMENT DB ==============

def get_player_axe_level(user_id: int) -> int:
    """Получить уровень топора игрока (0 = нет топора)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT axe_level FROM player_axes WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def set_player_axe_level(user_id: int, level: int):
    """Установить уровень топора игрока"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO player_axes (user_id, axe_level) VALUES (?, ?)', (user_id, level))
    conn.commit()
    conn.close()

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


# ============== LEADERBOARD ==============

def get_leaderboard(limit: int = 10):
    """Получить рейтинг игроков (по очкам рейтинга, победам, силе)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT nickname, strength, COALESCE(wins, 0), COALESCE(rating_points, 0) FROM players
        WHERE strength > 0
        ORDER BY rating_points DESC, wins DESC, strength DESC
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_leaderboard_page(page: int = 0, per_page: int = 5):
    """Получить страницу рейтинга игроков с пагинацией"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Общее количество
    cursor.execute('SELECT COUNT(*) FROM players WHERE strength > 0')
    total = cursor.fetchone()[0]
    
    offset = page * per_page
    cursor.execute('''
        SELECT nickname, strength, COALESCE(wins, 0), COALESCE(rating_points, 0),
               COALESCE(status, 'Новичок'), COALESCE(crystals, 0) FROM players
        WHERE strength > 0
        ORDER BY rating_points DESC, wins DESC, strength DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    
    results = cursor.fetchall()
    conn.close()
    
    total_pages = max(1, (total + per_page - 1) // per_page)
    return results, total_pages, total


# ============== RATING ==============

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


def get_rating_league(rating_points: int) -> str:
    """Получить название лиги по очкам рейтинга"""
    if rating_points < 100:
        return "🎗 Новичковая лига"
    elif rating_points < 200:
        return "🌟 Серебряная лига"
    elif rating_points < 350:
        return "🌟 Любительская лига"
    elif rating_points < 500:
        return "📕 Продвинутая лига"
    elif rating_points < 800:
        return f"{E_GIFT} Избранная лига"
    elif rating_points < 1150:
        return f"{E_GIFT} Профессиональная лига"
    elif rating_points < 1500:
        return f"{E_GIFT} Киберспортивная лига"
    else:
        return f"{E_GIFT} Мировая лига"


def get_pvp_league_points(rating_points: int) -> tuple:
    """Вернуть (очки за победу, очки за поражение) для текущей лиги"""
    if rating_points < 100:
        return (12, 3)
    elif rating_points < 200:
        return (10, 4)
    elif rating_points < 350:
        return (10, 4)
    elif rating_points < 500:
        return (9, 5)
    elif rating_points < 800:
        return (8, 6)
    elif rating_points < 1150:
        return (8, 7)
    elif rating_points < 1500:
        return (7, 9)
    else:
        return (5, 11)


# ============== CLAN DB FUNCTIONS ==============

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


# ============== CLAN BOSS DB FUNCTIONS ==============

def get_clan_boss(clan_id: int) -> dict:
    """Получить текущего кланового босса из БД. Создаёт запись если нет."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT boss_num, current_health, last_defeated_at, status FROM clan_bosses WHERE clan_id = ?', (clan_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"boss_num": row[0], "current_health": row[1], "last_defeated_at": row[2], "status": row[3]}
    # Создать запись для нового клана
    boss_cfg = CLAN_BOSSES_CONFIG[1]
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO clan_bosses (clan_id, boss_num, current_health, status)
        VALUES (?, 1, ?, 'active')
    ''', (clan_id, boss_cfg['health']))
    conn.commit()
    conn.close()
    return {"boss_num": 1, "current_health": boss_cfg['health'], "last_defeated_at": None, "status": "active"}

def update_clan_boss_health(clan_id: int, new_health: int):
    """Обновить здоровье кланового босса"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE clan_bosses SET current_health = ? WHERE clan_id = ?', (new_health, clan_id))
    conn.commit()
    conn.close()

def defeat_clan_boss(clan_id: int, current_boss_num: int):
    """Отметить босса как побеждённого и поставить следующего на cooldown"""
    next_boss = 2 if current_boss_num == 1 else 1
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE clan_bosses
        SET status = 'cooldown', last_defeated_at = ?, boss_num = ?
        WHERE clan_id = ?
    ''', (now, next_boss, clan_id))
    # Сбросить урон участников
    cursor.execute('DELETE FROM clan_boss_damage WHERE clan_id = ?', (clan_id,))
    conn.commit()
    conn.close()

def check_and_respawn_clan_boss(clan_id: int) -> bool:
    """Проверить cooldown и возродить босса если время прошло. Возвращает True если босс активен."""
    boss = get_clan_boss(clan_id)
    if boss['status'] == 'active':
        return True
    if not boss['last_defeated_at']:
        # Нет данных - активировать босса
        _activate_clan_boss(clan_id, boss['boss_num'])
        return True
    try:
        defeated_at = datetime.fromisoformat(boss['last_defeated_at'])
        if defeated_at.tzinfo is None:
            defeated_at = defeated_at.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        _activate_clan_boss(clan_id, boss['boss_num'])
        return True
    now = datetime.now(timezone.utc)
    boss_cfg = CLAN_BOSSES_CONFIG.get(boss['boss_num'], CLAN_BOSSES_CONFIG[1])
    cooldown = boss_cfg['cooldown_minutes'] * 60
    if (now - defeated_at).total_seconds() >= cooldown:
        _activate_clan_boss(clan_id, boss['boss_num'])
        return True
    return False

def _activate_clan_boss(clan_id: int, boss_num: int):
    """Активировать нового босса"""
    boss_cfg = CLAN_BOSSES_CONFIG.get(boss_num, CLAN_BOSSES_CONFIG[1])
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO clan_bosses (clan_id, boss_num, current_health, status)
        VALUES (?, ?, ?, 'active')
    ''', (clan_id, boss_num, boss_cfg['health']))
    conn.commit()
    conn.close()

def skip_clan_boss_cooldown(clan_id: int) -> bool:
    """Пропустить cooldown кланового босса и немедленно активировать следующего.
    Возвращает True если был cooldown и он успешно сброшен, False если босс уже активен."""
    boss = get_clan_boss(clan_id)
    if boss['status'] == 'active':
        return False
    _activate_clan_boss(clan_id, boss['boss_num'])
    return True

def get_clan_boss_remaining_cooldown(clan_id: int) -> str:
    """Получить оставшееся время cooldown в виде строки"""
    boss = get_clan_boss(clan_id)
    if boss['status'] == 'active':
        return "0 мин"
    if not boss['last_defeated_at']:
        return "0 мин"
    try:
        defeated_at = datetime.fromisoformat(boss['last_defeated_at'])
        if defeated_at.tzinfo is None:
            defeated_at = defeated_at.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return "0 мин"
    boss_cfg = CLAN_BOSSES_CONFIG.get(boss['boss_num'], CLAN_BOSSES_CONFIG[1])
    cooldown = boss_cfg['cooldown_minutes'] * 60
    elapsed = (datetime.now(timezone.utc) - defeated_at).total_seconds()
    remaining = max(0, int(cooldown - elapsed))
    mins = remaining // 60
    secs = remaining % 60
    if mins > 0:
        return f"{mins} мин {secs} сек"
    return f"{secs} сек"

def get_clan_boss_tickets(user_id: int, clan_id: int) -> int:
    """Получить количество билетов кланового босса"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT tickets FROM clan_boss_tickets WHERE user_id = ? AND clan_id = ?', (user_id, clan_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    # Создать запись
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO clan_boss_tickets (user_id, clan_id, tickets) VALUES (?, ?, ?)', (user_id, clan_id, MAX_CLAN_BOSS_TICKETS))
    conn.commit()
    conn.close()
    return 3

def use_clan_boss_ticket(user_id: int, clan_id: int) -> bool:
    """Потратить 1 билет кланового босса. Возвращает True если успешно."""
    tickets = get_clan_boss_tickets(user_id, clan_id)
    if tickets <= 0:
        return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE clan_boss_tickets SET tickets = tickets - 1 WHERE user_id = ? AND clan_id = ?', (user_id, clan_id))
    conn.commit()
    conn.close()
    return True

def add_clan_boss_tickets(user_id: int, clan_id: int, amount: int) -> int:
    """Добавить билеты кланового босса игроку (не больше MAX_CLAN_BOSS_TICKETS). Возвращает новое кол-во билетов."""
    current = get_clan_boss_tickets(user_id, clan_id)
    new_tickets = min(current + amount, MAX_CLAN_BOSS_TICKETS)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO clan_boss_tickets (user_id, clan_id, tickets) VALUES (?, ?, ?) '
        'ON CONFLICT(user_id, clan_id) DO UPDATE SET tickets = ?',
        (user_id, clan_id, new_tickets, new_tickets)
    )
    conn.commit()
    conn.close()
    return new_tickets

def add_clan_boss_damage(user_id: int, clan_id: int, damage: int):
    """Добавить урон игрока по клановому боссу"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clan_boss_damage (user_id, clan_id, total_damage)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, clan_id) DO UPDATE SET total_damage = total_damage + excluded.total_damage
    ''', (user_id, clan_id, damage))
    conn.commit()
    conn.close()

def get_clan_boss_participants(clan_id: int) -> list:
    """Получить список участников боя с клановым боссом (кто нанёс урон)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM clan_boss_damage WHERE clan_id = ? AND total_damage > 0', (clan_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def _get_boss_coins_reward(player_strength: float, boss_cfg: dict) -> int:
    """Получить монеты за победу над клановым боссом в зависимости от силы игрока"""
    for threshold, coins in boss_cfg['rewards']['coins_by_strength']:
        if threshold is None or player_strength < threshold:
            return coins
    return boss_cfg['rewards']['coins_by_strength'][-1][1]


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

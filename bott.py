import asyncio
import logging
import sqlite3
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Ваш токен от BotFather
TOKEN = "Ваш токен"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
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
            last_click TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Добавить столбец wins, если его нет (миграция)
    try:
        cursor.execute('ALTER TABLE players ADD COLUMN wins INTEGER DEFAULT 0')
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
    
    conn.commit()
    conn.close()

def add_player(user_id: int, nickname: str):
    """Добавить нового игрока в БД"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO players (user_id, nickname, points, click_power, strength, wins)
            VALUES (?, ?, 0.0, 1.0, 20.0, 0)
        ''', (user_id, nickname))
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
        SELECT user_id, nickname, points, click_power, strength, wins, last_click FROM players
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
            "last_click": result[6]
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

def get_leaderboard(limit: int = 10):
    """Получить рейтинг игроков (по силе)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT nickname, strength, COALESCE(wins, 0) FROM players
        WHERE strength > 0
        ORDER BY strength DESC
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

# ============== UPGRADES ==============
UPGRADES = {
    1: {"power": 2.0, "cost": 20, "display": "💳 2 клика"},
    2: {"power": 4.0, "cost": 100, "display": "💳 4 клика"},
    3: {"power": 8.0, "cost": 250, "display": "💳 8 клика"},
    4: {"power": 12.0, "cost": 550, "display": "💳 12 клика"},
    5: {"power": 25.0, "cost": 1150, "display": "💳 25 клика"}
}

# ============== EQUIPMENT ==============
EQUIPMENT = {
    1: {"name": "деревянный меч", "strength": 15, "cost": 50, "emoji": "🗡️"},
    2: {"name": "железный меч", "strength": 30, "cost": 150, "emoji": "🗡️"},
    3: {"name": "золотой меч", "strength": 50, "cost": 350, "emoji": "🗡️"},
    4: {"name": "кожаная одежда", "strength": 60, "cost": 550, "emoji": "👕"},
    5: {"name": "гаечный ключ", "strength": 85, "cost": 850, "emoji": "🔧"}
}

# ============== ENEMIES ==============
ENEMIES = {
    1: {"name": "Гоблин", "health": 50, "reward": 30, "base_damage": 8},
    2: {"name": "Лучник", "health": 120, "reward": 60, "base_damage": 15},
    3: {"name": "Дровосек", "health": 300, "reward": 90, "base_damage": 25},
    4: {"name": "Гоблин-гигант", "health": 640, "reward": 120, "base_damage": 40},
    5: {"name": "Дух леса", "health": 950, "reward": 190, "base_damage": 60}
}

# ============== STATES ==============
class Registration(StatesGroup):
    waiting_for_nickname = State()

class ShopMenu(StatesGroup):
    viewing_shop = State()

class EquipmentMenu(StatesGroup):
    viewing_equipment = State()

class BattleState(StatesGroup):
    viewing_enemies = State()
    in_battle = State()
    enemy_attacking = State()
    battle_round = State()

class OnlineState(StatesGroup):
    searching = State()
    waiting_accept = State()
    in_pvp_battle = State()

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
        [KeyboardButton(text="🏪 Магазин"), KeyboardButton(text="⚔️ Враги")],
        [KeyboardButton(text="🎖️ Снаряжение"), KeyboardButton(text="🏆 Рейтинг")],
        [KeyboardButton(text="🌐 Онлайн")],
        [KeyboardButton(text="/профиль")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_shop_kb():
    """Меню магазина"""
    kb = []
    
    for upgrade_id, upgrade_info in UPGRADES.items():
        button_text = f"💲 {upgrade_info['display']} ({upgrade_info['cost']} мощи)"
        kb.append([KeyboardButton(text=button_text)])
    
    kb.append([KeyboardButton(text="❌ Выход")])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_equipment_kb():
    """Меню снаряжения"""
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
        [KeyboardButton(text="🛡️ Защиту")]
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
    
    response = f"Прогресс пошел! 💪\nТекущие очки: {new_points}\nМощь клика: {player['click_power']}"
    await message.answer(response)

# ============== PROFILE ==============
@dp.message(Command("профиль"))
@dp.message(F.text == "/профиль")
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Профиль не найден. Напиши /start")
        return
    
    health = calculate_player_health(player['strength'])
    damage = calculate_damage(player['strength'])
    
    response = (
        f"👤 Профиль игрока: {player['nickname']}\n"
        f"📊 Очки: {player['points']}\n"
        f"⚡ Мощь клика: {player['click_power']}\n"
        f"💪 Сила: {player['strength']}\n"
        f"❤️ Здоровье: {health}\n"
        f"⚔️ Урон: {damage}"
    )
    await message.answer(response, reply_markup=get_main_kb())

# ============== CLICK UPGRADES SHOP ==============
@dp.message(F.text == "🏪 Магазин")
async def open_shop(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    
    shop_text = "🏪 **МАГАЗИН УЛУЧШЕНИЙ КЛИКА**\n\n"
    shop_text += f"Твоя текущая мощь: {player['points']} ⚡\n\n"
    shop_text += "Доступные улучшения:\n"
    
    for upgrade_id, upgrade_info in UPGRADES.items():
        status = "✅ (уже куплено)" if has_purchased_click_upgrade(user_id, upgrade_id) else ""
        shop_text += f"\n💳 {upgrade_info['display']} → Стоимость: {upgrade_info['cost']} очков {status}"
    
    await message.answer(shop_text, reply_markup=get_shop_kb())
    await state.set_state(ShopMenu.viewing_shop)

@dp.message(ShopMenu.viewing_shop)
async def handle_shop_purchase(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text
    
    if text == "❌ Выход":
        await state.clear()
        await message.answer("Вернулись в главное меню!", reply_markup=get_main_kb())
        return
    
    upgrade_purchased = False
    
    for upgrade_id, upgrade_info in UPGRADES.items():
        if upgrade_info['display'] in text:
            if has_purchased_click_upgrade(user_id, upgrade_id):
                await message.answer("❌ Вы уже купили данное улучшение!", reply_markup=get_shop_kb())
                return
            
            if player['points'] < upgrade_info['cost']:
                await message.answer(
                    f"❌ Недостаточно очков!\nТребуется: {upgrade_info['cost']}\nУ вас есть: {player['points']}",
                    reply_markup=get_shop_kb()
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
        await message.answer("❌ Выберите корректное улучшение!", reply_markup=get_shop_kb())

# ============== EQUIPMENT SHOP ==============
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
    
    response = "🏆 **РЕЙТИНГ ИГРОКОВ**\n\n"
    
    for index, (nickname, strength, wins) in enumerate(leaderboard, 1):
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"{index}."
        response += f"{medal} {nickname} — {int(strength)}🗡️ {wins}🏆\n"
    
    await message.answer(response, reply_markup=get_main_kb())

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
            
            battle_log += f"☠️ {enemy_info['name']} повержен!\n\n"
            battle_log += f"✅ **ВЫ ПОБЕДИЛИ!**\n\n"
            battle_log += f"💰 Награда: +{reward} очков\n"
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
    
    elif action == "🛡️ Защиту":
        # Защита уменьшает полученный урон на 50%
        enemy_damage = int(round(data['enemy_damage'] * random.uniform(0.35, 0.65)))
        new_player_health = int(round(data['player_health'] - enemy_damage))
        
        battle_log = f"🛡️ **РАУНД БОЯ** 🛡️\n\n"
        battle_log += f"👤 {player['nickname']} встал в защиту!\n\n"
        battle_log += f"☠️ {enemy_info['name']} атакует!\n"
        battle_log += f"💥 Урон: {enemy_damage} (защита сработала!)\n\n"
        
        # Проверяем, жив ли игрок
        if new_player_health <= 0:
            battle_log += f"👤 {player['nickname']} повержен!\n\n"
            battle_log += f"❌ **ВЫ ПРОИГРАЛИ!**\n\n"
            battle_log += f"Ты был повержен {enemy_info['name']}..."
            
            await message.answer(battle_log, reply_markup=get_end_battle_kb())
            await state.clear()
            return
        
        # Игрок контратакует при защите (меньший урон)
        counter_damage = int(round(data['player_damage'] * 0.5 * random.uniform(0.8, 1.2)))
        new_enemy_health = int(round(data['enemy_health'] - counter_damage))
        
        battle_log += f"⚔️ Контратака!\n"
        battle_log += f"💥 Урон: {counter_damage}\n\n"
        
        # Проверяем, живого ли врага
        if new_enemy_health <= 0:
            reward = enemy_info['reward']
            new_points = round(player['points'] + reward, 1)
            update_player_points(user_id, new_points)
            
            battle_log += f"☠️ {enemy_info['name']} повержен!\n\n"
            battle_log += f"✅ **ВЫ ПОБЕДИЛИ!**\n\n"
            battle_log += f"💰 Награда: +{reward} очков\n"
            battle_log += f"Всего очков: {new_points}"
            
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
            battle_log += "✅ **ВЫ ПОБЕДИЛИ!**\n(+1 победа, очки не начисляются)"
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

    elif text == "🛡️ Защиту":
        # Защита: снижаем входящий урон
        taken = int(round(enemy_damage * random.uniform(0.35, 0.65)))
        new_my_health = int(round(my_health - taken))

        battle_log = f"🛡️ **PvP БОЙ** 🛡️\n\nТы встал в защиту!\n💥 Получено урона: {taken} (снижено)\n\n"

        if new_my_health <= 0:
            battle_log += "❌ **ВЫ ПРОИГРАЛИ!**"
            await message.answer(battle_log, reply_markup=get_end_battle_kb())
            pvp_pairs.pop(user_id, None)
            pvp_pairs.pop(opponent_id, None)
            await state.clear()

            if opponent_id:
                update_player_wins(opponent_id)
                opp_state = dp.fsm.resolve_context(bot, opponent_id, opponent_id)
                await opp_state.clear()
                try:
                    await bot.send_message(
                        chat_id=opponent_id,
                        text="✅ **ВЫ ПОБЕДИЛИ!**\n(+1 победа, очки не начисляются)",
                        reply_markup=get_end_battle_kb()
                    )
                except Exception:
                    pass
            return

        battle_log += (
            f"👤 Ты: ❤️ {new_my_health}\n"
            f"👤 Соперник: ❤️ {enemy_health}\n\n"
            "⏳ Ход соперника..."
        )
        await message.answer(battle_log, reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        # Моё здоровье уменьшилось, передаём ход
        await state.update_data(pvp_player_health=new_my_health, pvp_my_turn=False)

        if opponent_id:
            opp_state = dp.fsm.resolve_context(bot, opponent_id, opponent_id)
            opp_data = await opp_state.get_data()
            # С точки зрения соперника: их pvp_enemy_health (= наше здоровье) уменьшилось
            new_opp_enemy_health = int(round(opp_data.get('pvp_enemy_health', 0) - taken))
            await opp_state.update_data(
                pvp_enemy_health=new_opp_enemy_health,
                pvp_my_turn=True
            )
            try:
                await bot.send_message(
                    chat_id=opponent_id,
                    text=(
                        f"🛡️ **PvP БОЙ** 🛡️\n\n"
                        f"Соперник встал в защиту!\n\n"
                        f"👤 Ты: ❤️ {opp_data.get('pvp_player_health', 0)}\n"
                        f"👤 Соперник: ❤️ {new_opp_enemy_health}\n\n"
                        "🗡️ Твой ход!"
                    ),
                    reply_markup=get_battle_action_kb()
                )
            except Exception:
                pass
    else:
        await message.answer("Выбери действие!", reply_markup=get_battle_action_kb())

# ============== MAIN ==============
async def main():
    init_database()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")

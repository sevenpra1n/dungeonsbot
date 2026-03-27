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
TOKEN = "7981611699:AAGF64JmGXpXONsVMA1wUeHFPdBJfW2lVNI"

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
            last_click TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
            INSERT INTO players (user_id, nickname, points, click_power, strength)
            VALUES (?, ?, 0.0, 1.0, 20.0)
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
        SELECT user_id, nickname, points, click_power, strength, last_click FROM players
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
            "last_click": result[5]
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
    """Получить рейтинг игроков (только с > 0 очков)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT nickname, points FROM players
        WHERE points > 0
        ORDER BY points DESC
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

# Словарь для отслеживания cooldown клика
click_cooldowns = {}

# ============== KEYBOARDS ==============
def get_main_kb():
    """Главное меню"""
    kb = [
        [KeyboardButton(text="качать хуй")],
        [KeyboardButton(text="🏪 Магазин"), KeyboardButton(text="⚔️ Враги")],
        [KeyboardButton(text="🎖️ Снаряжение"), KeyboardButton(text="🏆 Рейтинг")],
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

# ============== HELPER FUNCTIONS ==============
def calculate_player_health(strength: float) -> float:
    """Рассчитать здоровье игрока (сила * 0.2)"""
    return round(strength * 0.2, 1)

def calculate_damage(strength: float) -> float:
    """Рассчитать урон (сила * 0.4)"""
    return round(strength * 0.4, 1)

def calculate_enemy_damage(enemy_id: int) -> float:
    """Рассчитать урон врага (здоровье врага * 0.4)"""
    enemy_health = ENEMIES[enemy_id]['health']
    return round(enemy_health * 0.4, 1)

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
        await message.answer("📊 Рейтинг пуст. Начните кликать!", reply_markup=get_main_kb())
        return
    
    response = "🏆 **РЕЙТИНГ ИГРОКОВ**\n\n"
    
    for index, (nickname, points) in enumerate(leaderboard, 1):
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"{index}."
        response += f"{medal} {nickname} — {points} ⚡\n"
    
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
        enemy_damage = round(data['enemy_damage'] * random.uniform(0.7, 1.3), 1)
        new_player_health = data['player_health'] - enemy_damage
        
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
        player_damage = round(data['player_damage'] * random.uniform(0.8, 1.2), 1)
        new_enemy_health = data['enemy_health'] - player_damage
        
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
        enemy_damage = round(data['enemy_damage'] * random.uniform(0.7, 1.3), 1)
        new_player_health = data['player_health'] - enemy_damage
        
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
        enemy_damage = round(data['enemy_damage'] * random.uniform(0.35, 0.65), 1)
        new_player_health = data['player_health'] - enemy_damage
        
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
        counter_damage = round(data['player_damage'] * 0.5 * random.uniform(0.8, 1.2), 1)
        new_enemy_health = data['enemy_health'] - counter_damage
        
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

# ============== MAIN ==============
async def main():
    init_database()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")

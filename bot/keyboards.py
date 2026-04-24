from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from bot.data.equipment import WEAPONS, ARMOR, EQUIPMENT
from bot.data.enemies import ENEMIES
from bot.data.skills import SKILLS
from bot.data.locations import LOCATIONS
from bot.data.market import MARKET_RAID_TICKET_PRICE
from bot.data.statuses import STATUSES, STATUSES_PER_PAGE, is_status_available, _get_status_requirement_text
from bot.database import has_purchased_skill, get_friendship_status, has_liked_player
from bot.utils import send_image_with_text


# ============== KEYBOARDS ==============
def get_main_kb():
    """Главное меню"""
    kb = [
        [KeyboardButton(text="🗺️ Карта"),      KeyboardButton(text="📦 Инвентарь")],
        [KeyboardButton(text="🔨 Кузня"),        KeyboardButton(text="🐉 Рейд")],
        [KeyboardButton(text="🌐 Онлайн"),       KeyboardButton(text="🛡️ Кланы")],
        [KeyboardButton(text="🏆 Рейтинг"),     KeyboardButton(text="📖 Профиль")],
        [KeyboardButton(text="👥 Друзья"),       KeyboardButton(text="🛒 Рынок")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_main_menu_text() -> str:
    """Текст главного меню"""
    return (
        '<tg-emoji emoji-id="5265000876870761765">🔖</tg-emoji> Главное меню Hades:\n'
        '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji>Текущий сезон: Season 1 <tg-emoji emoji-id="5906478942885255780">⭐</tg-emoji>\n'
        '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji>├ <tg-emoji emoji-id="5906852613629941703">🟢</tg-emoji> the initial expedition\n\n'
        '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji> Версия обновления:\n'
        '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji>├ <tg-emoji emoji-id="5906800644525660990">🟡</tg-emoji> Beta 1.1\n\n'
        '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji><tg-emoji emoji-id="5354857360844152098">#️⃣</tg-emoji> Кнопки команд ниже:'
    )

async def show_main_menu(message, state: FSMContext = None):
    """Показать главное меню с картинкой и кнопками"""
    if state:
        await state.clear()
    await send_image_with_text(message, "images/menu.png", get_main_menu_text(), reply_markup=get_main_kb())

def get_market_category_kb() -> ReplyKeyboardMarkup:
    """Клавиатура категорий рынка"""
    kb = [
        [KeyboardButton(text="🥕 Продажа ресурсов")],
        [KeyboardButton(text="📕 Расходники")],
        [KeyboardButton(text="🎁 Предметы")],
        [KeyboardButton(text="⬅️ Назад в меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_market_kb() -> ReplyKeyboardMarkup:
    """Клавиатура рынка (продажа ресурсов)"""
    kb = [
        [KeyboardButton(text="Продать еду🥕"),        KeyboardButton(text="Продать древесину🌳")],
        [KeyboardButton(text="Продать камень🪨"),      KeyboardButton(text="Продать железо⛰")],
        [KeyboardButton(text="Продать золото🥇")],
        [KeyboardButton(text="⬅️ Назад к категориям")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_consumables_kb() -> ReplyKeyboardMarkup:
    """Клавиатура расходников"""
    kb = [
        [KeyboardButton(text=f"Купить билет рейда ({MARKET_RAID_TICKET_PRICE}💰)")],
        [KeyboardButton(text="⬅️ Назад к категориям")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_sell_qty_kb(material: str, inv_amount: int) -> ReplyKeyboardMarkup:
    """Клавиатура выбора количества для продажи"""
    kb = []
    # Offer quantities: 1, 5, 10, 25, 50, all
    row = []
    for qty in [1, 5, 10, 25, 50]:
        if inv_amount >= qty:
            row.append(KeyboardButton(text=f"Продать {qty}"))
            if len(row) == 3:
                kb.append(row)
                row = []
    if row:
        kb.append(row)
    if inv_amount > 0:
        kb.append([KeyboardButton(text=f"Продать всё ({inv_amount})")])
    kb.append([KeyboardButton(text="⬅️ Назад на рынок")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_forge_kb():
    """Главное меню кузни"""
    kb = [
        [KeyboardButton(text="⚔️ Оружие"), KeyboardButton(text="🛡️ Броня")],
        [KeyboardButton(text="✨ Скиллы")],
        [KeyboardButton(text="❌ Выход")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def _weapon_btn_text(w: dict) -> str:
    """Текст кнопки оружия (используется в KB и при matching)"""
    return f"⚔️ {w['name']} — {w['cost']} монет"


def _armor_btn_text(a: dict) -> str:
    """Текст кнопки брони (используется в KB и при matching)"""
    return f"🛡️ {a['name']} — {a['cost']} монет"


def get_weapons_kb():
    """Меню выбора оружия"""
    kb = []
    for w_id, w_info in WEAPONS.items():
        btn = _weapon_btn_text(w_info)
        kb.append([KeyboardButton(text=btn)])
    kb.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_armor_kb():
    """Меню выбора брони"""
    kb = []
    for a_id, a_info in ARMOR.items():
        btn = _armor_btn_text(a_info)
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

def get_raid_menu_kb(has_coop_partner: bool = False) -> ReplyKeyboardMarkup:
    """Меню рейда (до начала боя). Показывает кнопку co-op только когда партнёр принял приглашение."""
    kb = []
    if has_coop_partner:
        kb.append([KeyboardButton(text="🤝 Начать совместный рейд")])
    kb.append([KeyboardButton(text="⚔️ Начать рейд"), KeyboardButton(text="❌ Выйти")])
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

def get_online_menu_kb():
    """Главное меню онлайн-режима (лобби)"""
    kb = [
        [KeyboardButton(text="🔍 Поиск игрока")],
        [KeyboardButton(text="📋 О лигах")],
        [KeyboardButton(text="❌ Выйти из онлайна")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_clan_boss_menu_kb() -> ReplyKeyboardMarkup:
    """Клавиатура меню кланового босса"""
    kb = [
        [KeyboardButton(text="⚔️ помочь одолеть босса")],
        [KeyboardButton(text="🔙 Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_clan_boss_battle_kb(user_id: int = None, mana: int = 100) -> ReplyKeyboardMarkup:
    """Клавиатура боя с клановым боссом (динамическая: добавляет кнопки скиллов)"""
    kb = [
        [KeyboardButton(text="⚔️ Атаковать")],
    ]
    if user_id is not None:
        for skill_id, skill in SKILLS.items():
            if has_purchased_skill(user_id, skill_id) and mana >= skill['mana_cost']:
                kb.append([KeyboardButton(text=f"✨ Скилл {skill_id}: {skill['name']}")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_clan_boss_back_kb() -> ReplyKeyboardMarkup:
    """Клавиатура возврата из кланового босса"""
    kb = [
        [KeyboardButton(text="🔙 Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_rating_kb(leaderboard, page: int, total_pages: int):
    """Меню рейтинга с кнопками игроков и пагинацией"""
    kb = []
    for row in leaderboard:
        nickname = row[0]
        kb.append([KeyboardButton(text=f"👤 {nickname}")])
    nav = []
    if page > 0:
        nav.append(KeyboardButton(text="⬅️ Назад"))
    if page < total_pages - 1:
        nav.append(KeyboardButton(text="Далее ➡️"))
    if nav:
        kb.append(nav)
    kb.append([KeyboardButton(text="❌ Выход")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_rating_player_kb(viewer_id: int = None, target_id: int = None):
    """Кнопка возврата из профиля игрока в рейтинг + кнопка друзей"""
    kb = []
    if viewer_id and target_id and viewer_id != target_id:
        fs = get_friendship_status(viewer_id, target_id)
        if fs == 'none':
            kb.append([KeyboardButton(text="➕ Добавить в друзья")])
        elif fs == 'accepted':
            kb.append([KeyboardButton(text="✅ В друзьях")])
        elif fs == 'pending_sent':
            kb.append([KeyboardButton(text="⏳ Заявка отправлена")])
        elif fs == 'pending_received':
            kb.append([KeyboardButton(text="➕ Добавить в друзья")])
        # Like button — shown only if not already liked
        if not has_liked_player(viewer_id, target_id):
            kb.append([KeyboardButton(text="❤️ Лайк")])
        else:
            kb.append([KeyboardButton(text="❤️ Лайкнуто")])
    kb.append([KeyboardButton(text="⬅️ Назад в рейтинг")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_pvp_accept_kb():
    """Меню подтверждения PvP"""
    kb = [
        [KeyboardButton(text="✅ Принять игру")],
        [KeyboardButton(text="❌ Отклонить")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_coop_invite_kb() -> ReplyKeyboardMarkup:
    """Клавиатура принятия/отклонения co-op приглашения"""
    kb = [
        [KeyboardButton(text="✅ Принять рейд")],
        [KeyboardButton(text="❌ Отклонить рейд")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_coop_lobby_kb() -> ReplyKeyboardMarkup:
    """Клавиатура лобби co-op (ожидание старта от организатора)"""
    kb = [
        [KeyboardButton(text="❌ Отменить рейд")],
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
        btn = _weapon_btn_text(w)
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
        btn = _armor_btn_text(a)
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
    kb.append([KeyboardButton(text="🏰 Клановый босс")])
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
        [KeyboardButton(text="🎟️ Накрутить билеты босса")],
        [KeyboardButton(text="🥕 Накрутить материалы")],
        [KeyboardButton(text="📦 Накрутить сундуки")],
        [KeyboardButton(text="⏩ Пропустить кд босса")],
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
    if location_id == 2:
        kb.append([KeyboardButton(text="💀 Поиск врага (30с)")])
    if location_id == 3:
        kb.append([KeyboardButton(text="💀 Поиск врага (60с)")])
    kb.append([KeyboardButton(text="⬅️ Назад на карту")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_profile_kb() -> ReplyKeyboardMarkup:
    """Клавиатура профиля"""
    kb = [
        [KeyboardButton(text="🎭 Статусы"), KeyboardButton(text="📦 Инвентарь")],
        [KeyboardButton(text="🏠 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_statuses_kb(player: dict, page: int = 0) -> ReplyKeyboardMarkup:
    """Клавиатура статусов с пагинацией (5 на страницу)"""
    all_ids = sorted(STATUSES.keys())
    total_pages = max(1, (len(all_ids) + STATUSES_PER_PAGE - 1) // STATUSES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * STATUSES_PER_PAGE
    end = start + STATUSES_PER_PAGE
    page_ids = all_ids[start:end]

    kb = []
    for s_id in page_ids:
        s = STATUSES[s_id]
        owned = (player.get('status') == s['name'])
        can_unlock = is_status_available(player, s)
        if owned:
            label = f"{s['emoji']} {s['name']} [✅ Активен]"
        elif can_unlock:
            label = f"{s['emoji']} {s['name']} [Выбрать]"
        else:
            req_text = _get_status_requirement_text(s)
            label = f"{s['emoji']} {s['name']} [{req_text}]"
        kb.append([KeyboardButton(text=label)])

    nav = []
    if page > 0:
        nav.append(KeyboardButton(text="⬅️ Пред. страница"))
    if page < total_pages - 1:
        nav.append(KeyboardButton(text="След. страница ➡️"))
    if nav:
        kb.append(nav)
    kb.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

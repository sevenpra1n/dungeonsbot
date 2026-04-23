"""All remaining message handlers (inventory, locations, forge, equipment,
rating, friends, raid, coop_raid, battle, main_menu, online_pvp, clans,
admin, market, clan_boss)."""

import asyncio
import html
import logging
import random
from datetime import datetime, timezone

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.loader import bot
from bot.config import ADMIN_IDS, BAGOUSER_ID, DB_NAME
from bot.emojis import *
from bot.states import (
    Registration, EquipmentMenu, ForgeMenu, BattleState, RaidState,
    OnlineState, ClanMenu, AdminPanel, LocationMenu, ProfileMenu,
    MarketMenu, RatingState, FriendsMenu, ClanBossState, CoopRaidState,
    LikeState,
)
from bot.global_state import (
    battle_cooldowns, pvp_queue, pvp_pairs,
    coop_raid_invites, coop_raid_pairs,
    clan_chat_sessions, clan_chat_spam_tracker,
)
from bot.database import (
    get_player, add_player, get_player_by_nickname,
    update_player_points, update_player_strength, update_player_wins,
    update_player_materials, update_player_raid_floor, update_player_raid_max_floor,
    add_points_to_player, add_strength_to_player, add_coins_to_player,
    remove_coins_from_player, add_crystals_to_player, add_raid_tickets_to_player,
    remove_raid_ticket, add_online_match, add_experience_to_player,
    get_experience_progress, get_player_status_emoji, set_player_status,
    send_friend_request, accept_friend_request, decline_friend_request,
    remove_friend, get_friends_list, get_friend_requests, get_friends_count,
    get_friendship_status, increment_player_deaths, increment_player_dodges,
    increment_player_pve_wins, has_liked_player, give_like_to_player,
    set_player_clan_image_flag, set_player_spammer_flag,
    get_inventory, add_inventory_material, add_all_inventory_materials,
    add_admin_materials_to_player, remove_inventory_material,
    get_components, add_component,
    get_unlocked_chest_statuses, unlock_chest_status, get_player_with_chest_statuses,
    start_activity, get_active_activity, finish_activity, check_activity_done,
    get_player_axe_level, set_player_axe_level,
    has_purchased_equipment, add_equipment_purchase,
    get_player_weapon, get_player_armor, set_player_weapon, set_player_armor,
    get_leaderboard, get_leaderboard_page,
    get_clan_boss, update_clan_boss_health, defeat_clan_boss,
    check_and_respawn_clan_boss, skip_clan_boss_cooldown,
    get_clan_boss_remaining_cooldown, get_clan_boss_tickets,
    use_clan_boss_ticket, add_clan_boss_tickets, add_clan_boss_damage,
    get_clan_boss_participants,
    get_player_clan, get_clan, create_clan, join_clan, leave_clan,
    kick_clan_member, delete_clan, set_clan_min_power, add_clan_exp,
    get_all_clans, get_clan_members, get_clan_member_role, set_clan_member_role,
    get_clan_co_leaders, update_clan_name, update_clan_description,
    update_clan_image, save_clan_message, get_clan_messages,
    get_player_skills, has_purchased_skill, add_skill_purchase,
    update_rating_points, get_pvp_league_points,
    ALLOWED_INVENTORY_MATERIALS,
    init_database,
)
from bot.utils import (
    calculate_player_health, calculate_damage, calculate_enemy_damage,
    can_battle_action, reset_battle_cooldown,
    apply_clan_strength_buff, get_clan_click_bonus, roll_miss,
    safe_html_answer, send_image_with_text, format_profile_text,
)
from bot.keyboards import (
    get_main_kb, get_main_menu_text, show_main_menu,
    get_forge_kb, get_weapons_kb, get_armor_kb, get_equipment_kb,
    get_enemies_kb, get_battle_kb, get_battle_action_kb, get_end_battle_kb,
    get_raid_menu_kb, get_searching_kb, get_online_menu_kb, get_pvp_accept_kb,
    get_rating_kb, get_rating_player_kb,
    get_clans_list_kb, get_create_clan_confirm_kb, get_my_clan_kb,
    get_kick_members_kb, get_promote_members_kb, get_demote_members_kb,
    get_clan_chat_kb, get_delete_clan_confirm_kb,
    get_admin_kb, get_map_kb, get_location_activities_kb,
    get_profile_kb, get_statuses_kb,
    get_market_category_kb, get_market_kb, get_consumables_kb, get_sell_qty_kb,
    get_clan_boss_menu_kb, get_clan_boss_battle_kb, get_clan_boss_back_kb,
    get_next_weapon_kb, get_next_armor_kb, get_skills_kb,
    get_monster_encounter_kb, get_coop_invite_kb, get_coop_lobby_kb,
    _weapon_btn_text, _armor_btn_text,
)
from bot.data.enemies import ENEMIES, RAID_FLOORS, COOP_ENEMY_HP_MULT, COOP_REWARD_MULT
from bot.data.equipment import EQUIPMENT, DEFAULT_WEAPON, DEFAULT_ARMOR, WEAPONS, ARMOR
from bot.data.locations import (
    LOCATIONS, LOCATION_ENEMIES, AXES, FOREST_ENEMIES,
    get_location_enemy_for_player, get_forest_enemy_for_player,
)
from bot.data.clans import (
    CLAN_LEVEL_EXP, MAX_CLAN_LEVEL, CLAN_BUFFS, CLAN_CHAT_MAX_MSG_LEN,
    BOSS_HEALTH_MULTIPLIER, MAX_CLAN_BOSS_TICKETS,
    TICKET_REFRESH_INTERVAL_SECONDS, CLAN_BOSSES_CONFIG,
)
from bot.data.chests import CHEST_CONFIG
from bot.data.statuses import (
    STATUSES, STATUSES_PER_PAGE, is_status_available,
    _get_status_requirement_text, _format_statuses_text,
)
from bot.data.skills import SKILLS
from bot.data.market import (
    MARKET_PRICES, MARKET_RAID_TICKET_PRICE,
    _MARKET_MAT_INFO, _MARKET_SELL_BUTTONS,
)
from bot.emojis import get_rarity_emoji
from bot.data.inventory_config import format_inventory_text
from bot.data.components_config import format_components_text
from bot.data.chests_config import CHEST_DISPLAY, format_chest_opening, format_chest_reward
from bot.data.leagues_config import get_league_label
from bot.data.emojis import (
    E_INV_HEADER, E_FRIENDS,
    E_GIFT as E_GIFT_NEW, E_GIFT2, E_GIFT3,
    E_RED,
)

router = Router()

# ============== INVENTORY TAB ==============
def _get_inventory_kb(back_button: str = "⬅️ Назад") -> ReplyKeyboardMarkup:
    """Клавиатура главного инвентаря"""
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📦 Компоненты"), KeyboardButton(text="🎁 Сундуки")],
        [KeyboardButton(text=back_button)],
    ], resize_keyboard=True)

def _get_chests_kb() -> ReplyKeyboardMarkup:
    """Клавиатура сундуков"""
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📦 Деревянный сундук")],
        [KeyboardButton(text="🔩 Стальной сундук")],
        [KeyboardButton(text="🌟 Золотой сундук")],
        [KeyboardButton(text="👑 Всевышний сундук")],
        [KeyboardButton(text="⬅️ Назад в инвентарь")],
    ], resize_keyboard=True)

async def _send_inventory(message, user_id: int, back_button: str = "⬅️ Назад"):
    """Показать инвентарь игрока (ресурсы)"""
    player = get_player(user_id)
    inv = get_inventory(user_id)
    nickname = html.escape(player['nickname']) if player else "Игрок"
    text = (
        f'{E_INV_HEADER} | Инвентарь {nickname}:\n'
        + format_inventory_text(inv)
    )
    await send_image_with_text(message, "images/inventory.png", text,
                               reply_markup=_get_inventory_kb(back_button))

async def _send_components(message, user_id: int):
    """Показать компоненты игрока"""
    comp = get_components(user_id)
    total = comp["common"] + comp["rare"] + comp["epic"] + comp["legendary"] + comp["mythic"]
    text = format_components_text(comp, total)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⬅️ Назад в инвентарь")]], resize_keyboard=True)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

async def _send_chests(message, user_id: int):
    """Показать сундуки игрока"""
    inv = get_inventory(user_id)
    chest_icon = CHEST_DISPLAY["chest_wood"]["emoji"]
    text = f'{chest_icon} Твои сундуки:\n\n'
    for key, info in CHEST_DISPLAY.items():
        count = inv.get(key, 0)
        text += (
            f'{info["emoji"]} {info["name"]}:\n'
            f'├ Количество: {count}\n'
            f'├ Дроп: {info["drop_label"]}\n\n'
        )
    await message.answer(text, reply_markup=_get_chests_kb(), parse_mode="HTML")


def _roll_chest_drops(user_id: int, chest_key: str) -> tuple[list[str], dict]:
    """
    Бросить дроп для сундука chest_key.
    Возвращает (lines, rewards) где lines — список строк для отображения,
    rewards — словарь {material: amount, 'experience': amount, 'coins': amount, 'crystals': amount, 'status': name}
    """
    cfg = CHEST_CONFIG[chest_key]
    lines = []
    rewards: dict = {}
    unlocked_statuses = get_unlocked_chest_statuses(user_id)

    for drop in cfg["drops"]:
        # drop formats:
        # ("coins",      (min, max))
        # ("experience", amount)
        # ("material",   amount)
        # ("material",   amount,    chance)
        # ("material",   (min, max), chance)
        # ("status",     "Name",    chance)
        if drop[0] == "status":
            _, sname, chance = drop
            if sname in unlocked_statuses:
                continue  # уже разблокирован — пропускаем
            if random.random() < chance:
                unlock_chest_status(user_id, sname)
                # Сразу устанавливаем статус
                set_player_status(user_id, sname)
                lines.append(f"{E_GIFT} Статус «{sname}» разблокирован!")
            continue

        resource = drop[0]
        if len(drop) == 2:
            # guaranteed
            val = drop[1]
            amount = random.randint(val[0], val[1]) if isinstance(val, tuple) else val
            chance = 1.0
            rolled = True
        else:
            val = drop[1]
            chance = drop[2]
            rolled = random.random() < chance
            if not rolled:
                continue
            amount = random.randint(val[0], val[1]) if isinstance(val, tuple) else val

        if amount <= 0:
            continue

        if resource == "coins":
            rewards['coins'] = rewards.get('coins', 0) + amount
            lines.append(f"{E_PLUS} +{amount} {E_COINS} монет")
        elif resource == "crystals":
            rewards['crystals'] = rewards.get('crystals', 0) + amount
            lines.append(f"{E_PLUS} +{amount} {E_CRYSTALS} кристаллов")
        elif resource == "experience":
            rewards['experience'] = rewards.get('experience', 0) + amount
            lines.append(f"{E_PLUS} +{amount} {E_STAR} опыта профиля")
        else:
            rewards[resource] = rewards.get(resource, 0) + amount
            mat_emojis = {
                'wood':     (E_WOOD,     'дерева'),
                'stone':    (E_STONE,    'камня'),
                'food':     (E_FOOD,     'еды'),
                'iron':     (E_IRON,     'железа'),
                'gold':     (E_GOLD_M,   'золота'),
                'copper':   (E_COPPER,   'меди'),
                'steel':    (E_STEEL,    'стали'),
                'amethyst': (E_AMETHYST, 'аметиста'),
                'gem':      (E_GEM,      'самоцвета'),
            }
            emoji, mat_name = mat_emojis.get(resource, ('📦', resource))
            lines.append(f"{E_PLUS} +{amount} {emoji} {mat_name}")

    return lines, rewards


async def _apply_chest_rewards(user_id: int, rewards: dict):
    """Применить награды сундука к игроку"""
    if rewards.get('coins'):
        add_coins_to_player(user_id, rewards['coins'])
    if rewards.get('crystals'):
        add_crystals_to_player(user_id, rewards['crystals'])
    if rewards.get('experience'):
        add_experience_to_player(user_id, rewards['experience'])
    for mat in ('wood', 'stone', 'food', 'iron', 'gold', 'copper', 'steel', 'amethyst', 'gem'):
        if rewards.get(mat):
            add_inventory_material(user_id, mat, rewards[mat])


CHEST_BUTTON_MAP = {
    "📦 Деревянный сундук": "chest_wood",
    "🔩 Стальной сундук":   "chest_steel",
    "🌟 Золотой сундук":    "chest_gold",
    "👑 Всевышний сундук":  "chest_divine",
}


@router.message(F.text == "📦 Инвентарь")
async def open_inventory_main(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    await state.set_state(ProfileMenu.viewing_inventory)
    await _send_inventory(message, user_id, back_button="🏠 В главное меню")


@router.message(ProfileMenu.viewing_inventory)
async def handle_inventory_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text in ("⬅️ Назад", "🏠 В главное меню"):
        data = await state.get_data()
        from_profile = data.get('inv_from_profile', False)
        if from_profile or text == "⬅️ Назад":
            player = get_player(user_id)
            await state.set_state(ProfileMenu.viewing_profile)
            if player:
                await _send_profile(message, player)
        else:
            await show_main_menu(message, state)
        return

    if text == "📦 Компоненты":
        await state.set_state(ProfileMenu.viewing_components)
        await _send_components(message, user_id)
        return

    if text == "🎁 Сундуки":
        await state.set_state(ProfileMenu.viewing_chests)
        await _send_chests(message, user_id)
        return

    await _send_inventory(message, user_id)


@router.message(ProfileMenu.viewing_components)
async def handle_components_menu(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад в инвентарь":
        await state.set_state(ProfileMenu.viewing_inventory)
        user_id = message.from_user.id
        data = await state.get_data()
        back = "🏠 В главное меню" if not data.get('inv_from_profile', False) else "⬅️ Назад"
        await _send_inventory(message, user_id, back_button=back)
        return
    await _send_components(message, message.from_user.id)


@router.message(ProfileMenu.viewing_chests)
async def handle_chests_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅️ Назад в инвентарь":
        await state.set_state(ProfileMenu.viewing_inventory)
        data = await state.get_data()
        back = "🏠 В главное меню" if not data.get('inv_from_profile', False) else "⬅️ Назад"
        await _send_inventory(message, user_id, back_button=back)
        return

    chest_key = CHEST_BUTTON_MAP.get(text)
    if chest_key:
        inv = get_inventory(user_id)
        if inv.get(chest_key, 0) <= 0:
            chest_name = CHEST_CONFIG[chest_key]["name"]
            await message.answer(
                f"{E_CROSS} У тебя нет {chest_name}а!",
                reply_markup=_get_chests_kb(), parse_mode="HTML"
            )
            return
        # Remove chest and start animation
        remove_inventory_material(user_id, chest_key, 1)
        await state.set_state(ProfileMenu.opening_chest)
        await state.update_data(opening_chest_key=chest_key)

        # Send animated open message using config formatter
        anim_msg = await message.answer(
            format_chest_opening(chest_key, 0), parse_mode="HTML"
        )
        await asyncio.sleep(2)

        for pct in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            await asyncio.sleep(0.4)
            try:
                await anim_msg.edit_text(
                    format_chest_opening(chest_key, pct), parse_mode="HTML"
                )
            except Exception:
                pass

        # Roll rewards
        lines, rewards = _roll_chest_drops(user_id, chest_key)
        await _apply_chest_rewards(user_id, rewards)

        chest_name = CHEST_CONFIG[chest_key]["name"]
        reward_text = "\n".join(lines) if lines else "Пусто…"
        result_text = (
            f'{E_GIFT} Вы открыли <b>{chest_name}</b>:\n\n'
            f'{reward_text}'
        )
        try:
            await anim_msg.edit_text(result_text, parse_mode="HTML")
        except Exception:
            await message.answer(result_text, parse_mode="HTML")

        await state.set_state(ProfileMenu.viewing_chests)
        await _send_chests(message, user_id)
        return

    await _send_chests(message, user_id)


@router.message(ProfileMenu.opening_chest)
async def handle_opening_chest(message: types.Message, state: FSMContext):
    """Пропустить ввод во время анимации открытия сундука"""
    pass

# ============== MAP / LOCATIONS ==============
@router.message(F.text == "🗺️ Карта")
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
            remaining = max(0, int((end_time - datetime.now(timezone.utc)).total_seconds()))
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

@router.message(LocationMenu.viewing_map)
async def handle_map(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "❌ Вернуться":
        await show_main_menu(message, state)
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
            loc_text = f"{loc['emoji']} <b>{loc['name']}</b>:\n\n{E_BOOK2} Выбери действие:\n"
            for act_key, act in loc['activities'].items():
                disp_emoji = act.get('display_emoji', act['emoji'])
                loc_text += f"\n{act['time']}s{E_HOURGLASS} │ {disp_emoji} │ {act['name']}\n"
            if loc_id == 1:
                loc_text += f"\n10s{E_HOURGLASS} | {E_SKULL} | Поиск врага\n"
            if loc_id == 2:
                loc_text += f"\n{E_SQ}{E_WARN} (необходим топор для добычи!)\n"
                loc_text += f"\n30s{E_HOURGLASS} | {E_SKULL} | Поиск врага\n"
            await send_image_with_text(message, loc.get('image', 'images/meadow.png'), loc_text, reply_markup=get_location_activities_kb(loc_id))
            await state.set_state(LocationMenu.viewing_location)
            return

    await message.answer("Выбери локацию из списка!", reply_markup=get_map_kb())

@router.message(LocationMenu.viewing_location)
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
            remaining = max(0, int((end_time - datetime.now(timezone.utc)).total_seconds()))
            await message.answer(
                f"⏳ У тебя уже идёт активность! Осталось: {remaining} сек.",
                reply_markup=get_location_activities_kb(loc_id)
            )
            return

    for act_key, act in loc['activities'].items():
        btn_text = f"{act['emoji']} {act['name']} ({act['time']}с)"
        if text == btn_text:
            # Check if axe is needed for forest wood chopping
            if loc_id == 2 and act_key == 'chop_wood':
                axe_level = get_player_axe_level(user_id)
                if axe_level <= 0:
                    await message.answer(
                        f"{E_CROSS} Необходим топор для добычи древесины!\nКупи топор в магазине (Рынок → Предметы).",
                        reply_markup=get_location_activities_kb(loc_id)
                    )
                    return
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
            reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True),
            parse_mode="HTML"
        )
        asyncio.create_task(_run_enemy_search(user_id, message.chat.id, search_time=10, location_id=1))
        return

    if text == "💀 Поиск врага (30с)":
        await state.set_state(LocationMenu.searching_enemy)
        await message.answer(
            f"{E_SKULL} <b>Поиск врага...</b>\n\n⏳ Осталось 30 секунд. Подожди — кнопки заблокированы.",
            reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True),
            parse_mode="HTML"
        )
        asyncio.create_task(_run_enemy_search(user_id, message.chat.id, search_time=30, location_id=2))
        return

    await message.answer("Выбери действие!", reply_markup=get_location_activities_kb(loc_id))

async def _run_enemy_search(user_id: int, chat_id: int, search_time: int = 10, location_id: int = 1):
    """Фоновая задача: ждёт search_time секунд, затем спаунит врага и начинает бой"""
    await asyncio.sleep(search_time)

    player = get_player(user_id)
    if not player:
        return

    fsm_ctx = dp.fsm.resolve_context(bot, chat_id, user_id)

    # Check still in searching_enemy state (player may have somehow left)
    current_state = await fsm_ctx.get_state()
    if current_state != LocationMenu.searching_enemy.state:
        return

    if location_id == 2:
        enemy_cfg = get_forest_enemy_for_player(player['strength'])
    else:
        enemy_cfg = get_location_enemy_for_player(player['strength'])
    enemy_strength = enemy_cfg['strength']
    # For forest enemies, use the explicit health value if available
    if 'health' in enemy_cfg:
        enemy_health = enemy_cfg['health']
    else:
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
        location_id=location_id,
    )

    battle_info = (
        f"{E_SKULL}{E_WARN} Враг найден!\n\n"
        f"{E_SQ}{E_RED_C} {enemy_cfg['name']}\n"
        f"{E_SQ}Сила: {enemy_cfg.get('strength', enemy_strength)} {E_ATK}\n"
        f"{E_SQ}Здоровье: {enemy_health} {E_ESWORD}\n"
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

@router.message(LocationMenu.searching_enemy)
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
    # Special handling for Forest wood chopping (depends on axe level)
    if loc_id == 2 and act_type == 'chop_wood':
        axe_level = get_player_axe_level(user_id)
        if axe_level > 0:
            for axe_id, axe_data in AXES.items():
                if axe_id <= axe_level:
                    wood_amount = random.randint(axe_data['min_wood'], axe_data['max_wood'])
                    if 'wood' not in earned:
                        earned['wood'] = 0
                    earned['wood'] += wood_amount
    else:
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
        'experience': (E_EXP,    'Опыта'),
    }
    reward_lines = []
    for k, v in earned.items():
        emoji, name = mat_names.get(k, ('', k))
        reward_lines.append(f"{E_PLUS} {v} {emoji} {name}")

    loc_name = loc.get('name', '?')
    act_name = act_cfg.get('name', act_type)
    act_emoji = act_cfg.get('emoji', '')

    text = (
        f"{E_BELL} <b>Добыча окончена!</b>\n\n"
        f"Локация: {loc_name}\n"
        f"Действие: {act_emoji} {act_name}\n\n"
        f"{E_GIFT} <b>Получено:</b>\n"
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
@router.message(LocationMenu.viewing_map, F.text == "⚔️ Сразиться с монстром")
@router.message(LocationMenu.viewing_location, F.text == "⚔️ Сразиться с монстром")
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
        f"{E_SKULL}{E_WARN} Враг найден!\n\n"
        f"{E_SKULL} {enemy_info['name']}\n"
        f"{E_SQ}Сила: {enemy_damage} {E_ATK}\n"
        f"{E_SQ}Здоровье: {enemy_info['health']} {E_ESWORD}\n\n"
        f"{_fmt_player_stats(html.escape(player['nickname']), player_health, player_damage, mana)}\n"
    )
    await message.answer(battle_info, reply_markup=get_battle_kb())

@router.message(LocationMenu.viewing_map, F.text == "🏃 Убежать")
@router.message(LocationMenu.viewing_location, F.text == "🏃 Убежать")
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


def _build_forge_main_text(player: dict, weapon: dict, armor: dict) -> str:
    """Построить текст главного меню кузни"""
    total_strength = int(player['strength'])
    w_rarity = get_rarity_emoji(weapon.get('rarity', 'common'))
    a_rarity = get_rarity_emoji(armor.get('rarity', 'common'))
    return (
        f"{E_FORGE}{E_YELLOW} КУЗНЯ:\n\n"
        f"{E_SQ}{E_ATK} {total_strength} {E_GREEN} общая сила\n\n"
        f"{E_SQ}{E_SWORD}{E_LINK} {w_rarity} {weapon['name']}:\n"
        f"  ├ Сила: {weapon['strength']} {E_ATK2}\n\n"
        f"{E_SQ}{E_SHIELD}{E_LINK} {a_rarity} {armor['name']}\n"
        f"  ├ Сила: {armor['strength']} {E_ATK2}\n\n"
        f"{E_ITEMS_STAR}{E_HAMMER} Выбери раздел для улучшения:"
    )

@router.message(F.text == "🔨 Кузня")
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

    forge_text = _build_forge_main_text(player, weapon, armor)
    await send_image_with_text(message, "images/kusnya.png", forge_text, reply_markup=get_forge_kb())
    await state.set_state(ForgeMenu.viewing_forge)

@router.message(ForgeMenu.viewing_forge)
async def handle_forge_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text

    if text == "❌ Выход":
        await show_main_menu(message, state)
        return

    if text == "⚔️ Оружие":
        weapon_id = get_player_weapon(user_id)
        weapon = _get_weapon_info(weapon_id)
        w_rarity = get_rarity_emoji(weapon.get('rarity', 'common'))
        next_weapon_id = weapon_id + 1
        if next_weapon_id > max(WEAPONS.keys()):
            weapons_text = (
                f"{E_ATK} Твоё ОРУЖИЕ {E_PROFILE}\n\n"
                f"{E_PIN}{E_YELLOW} Текущее оружие: \n"
                f" ├ {w_rarity} {weapon['name']}\n"
                f" ├ Сила: {weapon['strength']} {E_ATK2}{E_ARROW_UP}\n"
                f"{E_SQ}Монеты: {player['coins']}{E_COINS}\n\n"
                "✅ Вы достигли максимума"
            )
        else:
            next_w = WEAPONS[next_weapon_id]
            nw_rarity = get_rarity_emoji(next_w.get('rarity', 'common'))
            weapons_text = (
                f"{E_ATK} Твоё ОРУЖИЕ {E_PROFILE}\n\n"
                f"{E_PIN}{E_YELLOW} Текущее оружие: \n"
                f" ├ {w_rarity} {weapon['name']}\n"
                f" ├ Сила: {weapon['strength']} {E_ATK2}{E_ARROW_UP}\n"
                f"{E_SQ}Монеты: {player['coins']}{E_COINS}\n\n"
                f"{E_SQ}{E_GREEN} Следующее улучшение:\n"
                f"{E_STAR} {nw_rarity} {next_w['name']}\n"
                f" ├ Сила: {next_w['strength']} {E_ATK2}{E_ARROW_UP}\n"
                f"{E_SQ}{E_CART} Цена апгрейда: {next_w['cost']}{E_COINS}"
            )
        await send_image_with_text(message, "images/weapon.png", weapons_text, reply_markup=get_next_weapon_kb(weapon_id))
        await state.set_state(ForgeMenu.viewing_weapons)
        return

    if text == "🛡️ Броня":
        armor_id = get_player_armor(user_id)
        armor = _get_armor_info(armor_id)
        a_rarity = get_rarity_emoji(armor.get('rarity', 'common'))
        next_armor_id = armor_id + 1
        if next_armor_id > max(ARMOR.keys()):
            armor_text = (
                f"{E_SHIELD} Твоя БРОНЯ {E_PROFILE}\n\n"
                f"{E_PIN}{E_YELLOW} Текущая броня: \n"
                f" ├ {a_rarity} {armor['name']}\n"
                f" ├ Сила: {armor['strength']} {E_ATK2}{E_ARROW_UP}\n"
                f"{E_SQ}Монеты: {player['coins']}{E_COINS}\n\n"
                "✅ Вы достигли максимума"
            )
        else:
            next_a = ARMOR[next_armor_id]
            na_rarity = get_rarity_emoji(next_a.get('rarity', 'common'))
            armor_text = (
                f"{E_SHIELD} Твоя БРОНЯ {E_PROFILE}\n\n"
                f"{E_PIN}{E_YELLOW} Текущая броня: \n"
                f" ├ {a_rarity} {armor['name']}\n"
                f" ├ Сила: {armor['strength']} {E_ATK2}{E_ARROW_UP}\n"
                f"{E_SQ}Монеты: {player['coins']}{E_COINS}\n\n"
                f"{E_SQ}{E_GREEN} Следующее улучшение:\n"
                f"{E_STAR} {na_rarity} {next_a['name']}\n"
                f" ├ Сила: {next_a['strength']} {E_ATK2}{E_ARROW_UP}\n"
                f"{E_SQ}{E_CART} Цена апгрейда: {next_a['cost']}{E_COINS}"
            )
        await send_image_with_text(message, "images/armor.png", armor_text, reply_markup=get_next_armor_kb(armor_id))
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

@router.message(ForgeMenu.viewing_weapons)
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
        forge_text = _build_forge_main_text(player, weapon, armor)
        await send_image_with_text(message, "images/kusnya.png", forge_text, reply_markup=get_forge_kb())
        await state.set_state(ForgeMenu.viewing_forge)
        return

    # Определить, какое оружие выбрал игрок (точное совпадение с текстом кнопки)
    if text == "✅ Вы достигли максимума":
        current_wid = get_player_weapon(user_id)
        await message.answer("✅ Вы уже достигли максимального уровня оружия!", reply_markup=get_next_weapon_kb(current_wid))
        return

    chosen_weapon_id = None
    for w_id, w_info in WEAPONS.items():
        btn = _weapon_btn_text(w_info)
        if text == btn:
            chosen_weapon_id = w_id
            break

    if chosen_weapon_id is None:
        current_wid = get_player_weapon(user_id)
        await message.answer(f"{E_CROSS} Выбери оружие из списка!", reply_markup=get_next_weapon_kb(current_wid))
        return

    current_weapon_id = get_player_weapon(user_id)
    current_weapon = _get_weapon_info(current_weapon_id)
    new_weapon = WEAPONS[chosen_weapon_id]

    if new_weapon['strength'] <= current_weapon['strength']:
        await message.answer(
            f"{E_CROSS} Нельзя надеть оружие слабее или равное текущему!\n"
            f"Текущее: {current_weapon['emoji']} {current_weapon['name']} (сила: {current_weapon['strength']})",
            reply_markup=get_next_weapon_kb(current_weapon_id)
        )
        return

    if player['coins'] < new_weapon['cost']:
        await message.answer(
            f"{E_CROSS} Недостаточно монет!\nТребуется: {new_weapon['cost']}\nУ вас есть: {player['coins']}",
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

    nw_rarity = get_rarity_emoji(new_weapon.get('rarity', 'common'))
    a_rarity = get_rarity_emoji(armor.get('rarity', 'common'))
    await message.answer(
        f"{E_GIFT_UP} Оружие улучшено!\n\n"
        f"{nw_rarity} {new_weapon['name']}\n\n"
        f"{E_SQ}{E_SWORD}{E_LINK} {nw_rarity} {new_weapon['name']}:\n"
        f"  ├ Сила: {new_weapon_strength} {E_ATK2}\n\n"
        f"{E_SQ}{E_SHIELD}{E_LINK} {a_rarity} {armor['name']}\n"
        f"  ├ Сила: {armor['strength']} {E_ATK2}\n\n"
        f"{E_SQ}{E_ATK} {int(new_total_strength)} {E_GREEN} общая сила\n\n"
        f"{E_CROSS} {new_weapon['cost']} {E_COINS} монет\n"
        f"{E_YELLOW} Осталось: {new_coins} {E_COINS} монет",
        reply_markup=get_next_weapon_kb(chosen_weapon_id)
    )

@router.message(ForgeMenu.viewing_armor)
async def handle_armor_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text

    if text == "⬅️ Назад":
        weapon_id = get_player_weapon(user_id)
        armor_id = get_player_armor(user_id)
        weapon = _get_weapon_info(weapon_id)
        armor = _get_armor_info(armor_id)
        forge_text = _build_forge_main_text(player, weapon, armor)
        await send_image_with_text(message, "images/kusnya.png", forge_text, reply_markup=get_forge_kb())
        await state.set_state(ForgeMenu.viewing_forge)
        return

    # Определить, какую броню выбрал игрок (точное совпадение с текстом кнопки)
    if text == "✅ Вы достигли максимума":
        current_aid = get_player_armor(user_id)
        await message.answer("✅ Вы уже достигли максимального уровня брони!", reply_markup=get_next_armor_kb(current_aid))
        return

    chosen_armor_id = None
    for a_id, a_info in ARMOR.items():
        btn = _armor_btn_text(a_info)
        if text == btn:
            chosen_armor_id = a_id
            break

    if chosen_armor_id is None:
        current_aid = get_player_armor(user_id)
        await message.answer(f"{E_CROSS} Выбери броню из списка!", reply_markup=get_next_armor_kb(current_aid))
        return

    current_armor_id = get_player_armor(user_id)
    current_armor = _get_armor_info(current_armor_id)
    new_armor = ARMOR[chosen_armor_id]

    if new_armor['strength'] <= current_armor['strength']:
        await message.answer(
            f"{E_CROSS} Нельзя надеть броню слабее или равную текущей!\n"
            f"Текущая: {current_armor['emoji']} {current_armor['name']} (сила: {current_armor['strength']})",
            reply_markup=get_next_armor_kb(current_armor_id)
        )
        return

    if player['coins'] < new_armor['cost']:
        await message.answer(
            f"{E_CROSS} Недостаточно монет!\nТребуется: {new_armor['cost']}\nУ вас есть: {player['coins']}",
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

    w_rarity = get_rarity_emoji(weapon.get('rarity', 'common'))
    na_rarity = get_rarity_emoji(new_armor.get('rarity', 'common'))
    await message.answer(
        f"{E_GIFT_UP} Броня улучшена!\n\n"
        f"{na_rarity} {new_armor['name']}\n\n"
        f"{E_SQ}{E_SWORD}{E_LINK} {w_rarity} {weapon['name']}:\n"
        f"  ├ Сила: {weapon['strength']} {E_ATK2}\n\n"
        f"{E_SQ}{E_SHIELD}{E_LINK} {na_rarity} {new_armor['name']}\n"
        f"  ├ Сила: {new_armor_strength} {E_ATK2}\n\n"
        f"{E_SQ}{E_ATK} {int(new_total_strength)} {E_GREEN} общая сила\n\n"
        f"{E_CROSS} {new_armor['cost']} {E_COINS} монет\n"
        f"{E_YELLOW} Осталось: {new_coins} {E_COINS} монет",
        reply_markup=get_next_armor_kb(chosen_armor_id)
    )

@router.message(ForgeMenu.viewing_skills)
async def handle_skills_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text

    if text == "⬅️ Назад":
        weapon_id = get_player_weapon(user_id)
        armor_id = get_player_armor(user_id)
        weapon = _get_weapon_info(weapon_id)
        armor = _get_armor_info(armor_id)
        forge_text = _build_forge_main_text(player, weapon, armor)
        await send_image_with_text(message, "images/kusnya.png", forge_text, reply_markup=get_forge_kb())
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
                    f'{E_CROSS} Недостаточно монет!\nТребуется: {skill["price"]} монет\nУ вас: {player["coins"]}',
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
@router.message(F.text == "🎖️ Снаряжение")
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

@router.message(EquipmentMenu.viewing_equipment)
async def handle_equipment_purchase(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text
    
    if text == "❌ Выход":
        await show_main_menu(message, state)
        return
    
    equipment_purchased = False
    
    for equip_id, equip_info in EQUIPMENT.items():
        if equip_info['name'] in text:
            if has_purchased_equipment(user_id, equip_id):
                await message.answer(f"{E_CROSS} Вы уже купили данное снаряжение!", reply_markup=get_equipment_kb())
                return
            
            if player['points'] < equip_info['cost']:
                await message.answer(
                    f"{E_CROSS} Недостаточно очков!\nТребуется: {equip_info['cost']}\nУ вас есть: {player['points']}",
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
        await message.answer(f"{E_CROSS} Выберите корректное снаряжение!", reply_markup=get_equipment_kb())

# ============== LEADERBOARD ==============
def _format_rating_page(leaderboard, page: int) -> str:
    """Форматировать страницу рейтинга"""
    response = f"{E_RATING} РЕЙТИНГ ИГРОКОВ\n\n"
    
    start_index = page * 5 + 1
    
    for i, row in enumerate(leaderboard):
        nickname, strength, wins, rating_pts, status, crystals = row
        index = start_index + i
        safe_nick = html.escape(nickname)
        safe_status = html.escape(status)
        # Get status emoji from STATUSES dict
        status_emoji = '🔸'
        for s in STATUSES.values():
            if s['name'] == status:
                status_emoji = s.get('custom_emoji', s['emoji'])
                break
        league = get_league_label(rating_pts)
        
        if index == 1:
            prefix = f"{E_STAR} 1. {E_GIFT_NEW}"
        elif index == 2:
            prefix = f"{E_YELLOW} 2. {E_GIFT2}"
        elif index == 3:
            prefix = f"{E_YELLOW} 3. {E_GIFT3}"
        else:
            prefix = f"{E_RED} {index}. {E_HASHTAG}"
        
        response += (
            f"{prefix} {E_PROFILE} {safe_nick}:\n"
            f"├ Статус: {status_emoji} {safe_status}\n\n"
            f"{int(strength)} {E_POW}\n"
            f"{wins} {E_TROPHY}\n"
            f"{crystals} 💠\n"
            f"├ Лига: {league}\n"
            f"├ Points {rating_pts} {E_STAR}\n\n"
        )
    
    return response

@router.message(F.text == "🏆 Рейтинг")
async def show_leaderboard(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    
    leaderboard, total_pages, total = get_leaderboard_page(0, 5)
    
    if not leaderboard:
        await message.answer("📊 Рейтинг пуст. Прокачайся!", reply_markup=get_main_kb())
        return
    
    response = _format_rating_page(leaderboard, 0)
    
    await state.set_state(RatingState.viewing_rating)
    await state.update_data(rating_page=0)
    await send_image_with_text(message, "images/league.png", response, reply_markup=get_rating_kb(leaderboard, 0, total_pages))


@router.message(RatingState.viewing_rating)
async def handle_rating_menu(message: types.Message, state: FSMContext):
    text = message.text
    
    if text == "❌ Выход":
        await show_main_menu(message, state)
        return
    
    data = await state.get_data()
    current_page = data.get('rating_page', 0)
    
    if text == "Далее ➡️":
        new_page = current_page + 1
        leaderboard, total_pages, total = get_leaderboard_page(new_page, 5)
        if not leaderboard:
            await message.answer("Больше игроков нет.")
            return
        response = _format_rating_page(leaderboard, new_page)
        await state.update_data(rating_page=new_page)
        await send_image_with_text(message, "images/league.png", response, reply_markup=get_rating_kb(leaderboard, new_page, total_pages))
        return
    
    if text == "⬅️ Назад":
        new_page = max(0, current_page - 1)
        leaderboard, total_pages, total = get_leaderboard_page(new_page, 5)
        response = _format_rating_page(leaderboard, new_page)
        await state.update_data(rating_page=new_page)
        await send_image_with_text(message, "images/league.png", response, reply_markup=get_rating_kb(leaderboard, new_page, total_pages))
        return
    
    # Check if player nickname button was pressed
    if text and text.startswith("👤 "):
        nickname = text[2:].strip()
        target = get_player_by_nickname(nickname)
        if target:
            full_player = get_player(target['user_id'])
            if full_player:
                health = calculate_player_health(full_player['strength'])
                damage = calculate_damage(full_player['strength'])
                exp_info = get_experience_progress(full_player['user_id'])
                status_emoji = get_player_status_emoji(full_player)
                league = get_league_label(full_player.get('rating_points', 0))
                profile_text = format_profile_text(
                    nickname=full_player["nickname"],
                    status=f"{status_emoji} {full_player['status']}",
                    level=full_player["player_level"],
                    current_exp=exp_info["current_exp"],
                    needed_exp=exp_info["needed_exp"],
                    rating_points=full_player.get("rating_points", 0),
                    league=league,
                    wins=full_player["wins"],
                    strength=int(full_player["strength"]),
                    health=health,
                    coins=full_player["coins"],
                    crystals=full_player["crystals"],
                    raid_tickets=full_player["raid_tickets"],
                    likes=full_player.get("likes", 0),
                )
                viewer_id = message.from_user.id
                await state.set_state(RatingState.viewing_player)
                await state.update_data(viewing_player_id=full_player['user_id'])
                await send_image_with_text(message, "images/profile.png", profile_text, reply_markup=get_rating_player_kb(viewer_id, full_player['user_id']))
                return
        await message.answer(f"{E_CROSS} Игрок не найден!")
        return


@router.message(RatingState.viewing_player, F.text == "⬅️ Назад в рейтинг")
async def back_to_rating(message: types.Message, state: FSMContext):
    data = await state.get_data()
    page = data.get('rating_page', 0)
    leaderboard, total_pages, total = get_leaderboard_page(page, 5)
    
    if not leaderboard:
        await show_main_menu(message, state)
        return
    
    response = _format_rating_page(leaderboard, page)
    await state.set_state(RatingState.viewing_rating)
    await send_image_with_text(message, "images/league.png", response, reply_markup=get_rating_kb(leaderboard, page, total_pages))

@router.message(RatingState.viewing_player, F.text == "➕ Добавить в друзья")
async def add_friend_from_rating(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    target_id = data.get('viewing_player_id')
    if not target_id:
        await message.answer("❌ Ошибка: игрок не найден.")
        return
    result = send_friend_request(user_id, target_id)
    if result == 'sent':
        await message.answer("✅ Заявка в друзья отправлена!")
        # Send notification to target player
        player = get_player(user_id)
        if player:
            safe_nick = html.escape(player['nickname'])
            try:
                await bot.send_message(
                    chat_id=target_id,
                    text=f"{E_PROFILE} 👤 {safe_nick} добавил тебя в друзья!\n\nПринять можно во вкладке «👥 Друзья» → «📩 Заявки в друзья»",
                    parse_mode="HTML"
                )
            except Exception:
                pass
        # Refresh the profile view with updated keyboard
        target_player = get_player(target_id)
        if target_player:
            health = calculate_player_health(target_player['strength'])
            exp_info = get_experience_progress(target_player['user_id'])
            status_emoji = get_player_status_emoji(target_player)
            league = get_league_label(target_player.get('rating_points', 0))
            profile_text = format_profile_text(
                nickname=target_player["nickname"],
                status=f"{status_emoji} {target_player['status']}",
                level=target_player["player_level"],
                current_exp=exp_info["current_exp"],
                needed_exp=exp_info["needed_exp"],
                rating_points=target_player.get("rating_points", 0),
                league=league,
                wins=target_player["wins"],
                strength=int(target_player["strength"]),
                health=health,
                coins=target_player["coins"],
                crystals=target_player["crystals"],
                raid_tickets=target_player["raid_tickets"],
                likes=target_player.get("likes", 0),
            )
            await send_image_with_text(message, "images/profile.png", profile_text, reply_markup=get_rating_player_kb(user_id, target_id))
        else:
            await message.answer("✅ Заявка отправлена!", reply_markup=get_rating_player_kb(user_id, target_id))
    elif result == 'already_friends':
        await message.answer("✅ Вы уже друзья!")
    elif result == 'already_pending':
        await message.answer("⏳ Заявка уже отправлена!")
    elif result == 'self':
        await message.answer("❌ Нельзя добавить себя в друзья!")

@router.message(RatingState.viewing_player, F.text.in_({"✅ В друзьях", "⏳ Заявка отправлена"}))
async def friend_status_info(message: types.Message, state: FSMContext):
    if message.text == "✅ В друзьях":
        await message.answer("✅ Этот игрок уже у вас в друзьях!")
    else:
        await message.answer("⏳ Заявка уже отправлена, ожидайте ответа!")

@router.message(RatingState.viewing_player, F.text.in_({"❤️ Лайк", "❤️ Лайкнуто"}))
async def like_from_rating(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    target_id = data.get('viewing_player_id')
    if not target_id:
        await message.answer(f"{E_CROSS} Ошибка: игрок не найден.")
        return
    if message.text == "❤️ Лайкнуто":
        await message.answer("❤️ Вы уже ставили лайк этому игроку!", reply_markup=get_rating_player_kb(user_id, target_id))
        return
    if has_liked_player(user_id, target_id):
        await message.answer("❤️ Вы уже ставили лайк этому игроку!", reply_markup=get_rating_player_kb(user_id, target_id))
        return
    # Ask for послание
    await state.set_state(LikeState.waiting_message_from_rating)
    await state.update_data(like_target_id=target_id, like_prev_player_id=target_id)
    cancel_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)
    await message.answer(
        f"{E_HP} Напишите послание для этого игрока:\n(оно будет отправлено вместе с лайком)",
        reply_markup=cancel_kb
    )

@router.message(LikeState.waiting_message_from_rating)
async def process_like_message_from_rating(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text or ""
    data = await state.get_data()
    target_id = data.get('like_target_id')

    if text == "❌ Отмена":
        await state.set_state(RatingState.viewing_player)
        target_player = get_player(target_id) if target_id else None
        if target_player:
            health = calculate_player_health(target_player['strength'])
            exp_info = get_experience_progress(target_player['user_id'])
            status_emoji = get_player_status_emoji(target_player)
            league = get_league_label(target_player.get('rating_points', 0))
            profile_text = format_profile_text(
                nickname=target_player["nickname"],
                status=f"{status_emoji} {target_player['status']}",
                level=target_player["player_level"],
                current_exp=exp_info["current_exp"],
                needed_exp=exp_info["needed_exp"],
                rating_points=target_player.get("rating_points", 0),
                league=league,
                wins=target_player["wins"],
                strength=int(target_player["strength"]),
                health=health,
                coins=target_player["coins"],
                crystals=target_player["crystals"],
                raid_tickets=target_player["raid_tickets"],
                likes=target_player.get("likes", 0),
            )
            await send_image_with_text(message, "images/profile.png", profile_text, reply_markup=get_rating_player_kb(user_id, target_id))
        return

    if not target_id:
        await state.set_state(RatingState.viewing_rating)
        await message.answer(f"{E_CROSS} Ошибка: игрок не найден.")
        return

    poslanie = text.strip()[:200]  # limit message length
    result = give_like_to_player(user_id, target_id, poslanie)
    await state.set_state(RatingState.viewing_player)
    if result:
        liker = get_player(user_id)
        target = get_player(target_id)
        if liker and target:
            safe_liker_nick = html.escape(liker['nickname'])
            safe_poslanie = html.escape(poslanie)
            try:
                await bot.send_message(
                    chat_id=target_id,
                    text=f"{E_HP} ваш профиль оценил {safe_liker_nick}!\n{safe_poslanie}",
                    parse_mode="HTML"
                )
            except Exception:
                pass
        await message.answer(f"❤️ Лайк и послание отправлены!", reply_markup=get_rating_player_kb(user_id, target_id))
    else:
        await message.answer("❤️ Вы уже ставили лайк этому игроку!", reply_markup=get_rating_player_kb(user_id, target_id))

# ============== FRIENDS MENU ==============
FRIENDS_PER_PAGE = 5

def get_friends_kb(friends_data: list, page: int, total_pages: int, has_requests: bool = False) -> ReplyKeyboardMarkup:
    """Клавиатура списка друзей с пагинацией"""
    kb = []
    for friend in friends_data:
        kb.append([KeyboardButton(text=f"👤 {friend['nickname']}")])
    nav = []
    if page > 0:
        nav.append(KeyboardButton(text="⬅️ Назад"))
    if page < total_pages - 1:
        nav.append(KeyboardButton(text="Далее ➡️"))
    if nav:
        kb.append(nav)
    if has_requests:
        kb.append([KeyboardButton(text="📩 Заявки в друзья")])
    kb.append([KeyboardButton(text="⬅️ Назад в меню")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_friend_requests_kb(requests_data: list) -> ReplyKeyboardMarkup:
    """Клавиатура заявок в друзья"""
    kb = []
    for req in requests_data:
        kb.append([
            KeyboardButton(text=f"✅ Принять: {req['nickname']}"),
            KeyboardButton(text=f"❌ Отклонить: {req['nickname']}")
        ])
    kb.append([KeyboardButton(text="⬅️ Назад в друзья")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_friend_profile_kb(can_invite_raid: bool = False, viewer_id: int = None, friend_id: int = None) -> ReplyKeyboardMarkup:
    """Клавиатура профиля друга"""
    kb = []
    if can_invite_raid:
        kb.append([KeyboardButton(text="⚔️ Пригласить в рейд")])
    # Like button — shown only if not already liked
    if viewer_id and friend_id and viewer_id != friend_id:
        if not has_liked_player(viewer_id, friend_id):
            kb.append([KeyboardButton(text="❤️ Лайк")])
        else:
            kb.append([KeyboardButton(text="❤️ Лайкнуто")])
    kb.append([KeyboardButton(text="❌ Удалить из друзей")])
    kb.append([KeyboardButton(text="⬅️ Назад в друзья")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def _get_friends_page_data(user_id: int, page: int) -> tuple:
    """Получить данные друзей для страницы. Возвращает (friends_data, total_pages, total)"""
    friends_ids = get_friends_list(user_id)
    total = len(friends_ids)
    total_pages = max(1, (total + FRIENDS_PER_PAGE - 1) // FRIENDS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * FRIENDS_PER_PAGE
    end = start + FRIENDS_PER_PAGE
    page_ids = friends_ids[start:end]
    friends_data = []
    for fid in page_ids:
        fp = get_player(fid)
        if fp:
            friends_data.append(fp)
    return friends_data, total_pages, total

@router.message(F.text == "👥 Друзья")
async def open_friends(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    await state.set_state(FriendsMenu.viewing_friends)
    await state.update_data(friends_page=0)
    await _send_friends_list(message, state, user_id, 0)

async def _send_friends_list(message, state: FSMContext, user_id: int, page: int):
    """Показать список друзей"""
    friends_data, total_pages, total = _get_friends_page_data(user_id, page)
    requests = get_friend_requests(user_id)
    has_requests = len(requests) > 0

    if total == 0:
        text = (
            f'<tg-emoji emoji-id="5386745190914482793">😢</tg-emoji> У вас пока нету друзей...\n'
            f'{E_SQ}<tg-emoji emoji-id="5276240711795107620">⚠️</tg-emoji> вы можете добавить друзей во вкладке "Рейтинг"!'
        )
        kb = []
        if has_requests:
            kb.append([KeyboardButton(text="📩 Заявки в друзья")])
        kb.append([KeyboardButton(text="⬅️ Назад в меню")])
        await message.answer(text, reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), parse_mode="HTML")
        return

    text = f'{E_FRIENDS} Всего в друзьях: {total}\n\n'
    start_index = page * FRIENDS_PER_PAGE
    for i, friend in enumerate(friends_data):
        idx = start_index + i + 1
        safe_nick = html.escape(friend['nickname'])
        status_emoji = get_player_status_emoji(friend)
        safe_status = html.escape(friend.get('status', 'Новичок'))
        league = get_league_label(friend.get('rating_points', 0))
        text += (
            f'{idx}. {E_PROFILE} {safe_nick}\n'
            f'  ├ Сила: {int(friend["strength"])} {E_POW}\n'
            f'  ├ Уровень: {friend["player_level"]} {E_STAR}\n'
            f'  ├ Статус: {status_emoji} {safe_status}\n'
            f'  ├ Лига: {league}\n\n'
        )

    await message.answer(text, reply_markup=get_friends_kb(friends_data, page, total_pages, has_requests), parse_mode="HTML")

@router.message(FriendsMenu.viewing_friends)
async def handle_friends_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅️ Назад в меню":
        await show_main_menu(message, state)
        return

    data = await state.get_data()
    current_page = data.get('friends_page', 0)

    if text == "Далее ➡️":
        new_page = current_page + 1
        await state.update_data(friends_page=new_page)
        await _send_friends_list(message, state, user_id, new_page)
        return

    if text == "⬅️ Назад":
        new_page = max(0, current_page - 1)
        await state.update_data(friends_page=new_page)
        await _send_friends_list(message, state, user_id, new_page)
        return

    if text == "📩 Заявки в друзья":
        await state.set_state(FriendsMenu.viewing_requests)
        await _send_friend_requests(message, user_id)
        return

    # Check if friend nickname button was pressed
    if text and text.startswith("👤 "):
        nickname = text[2:].strip()
        target = get_player_by_nickname(nickname)
        if target:
            full_player = get_player(target['user_id'])
            if full_player:
                await state.set_state(FriendsMenu.viewing_friend_profile)
                await state.update_data(viewing_friend_id=full_player['user_id'])
                await _send_friend_profile(message, full_player, viewer_id=user_id)
                return
        await message.answer(f"{E_CROSS} Друг не найден!")
        return

    await _send_friends_list(message, state, user_id, current_page)

async def _send_friend_profile(message, friend: dict, viewer_id: int = None):
    """Показать профиль друга"""
    health = calculate_player_health(friend['strength'])
    damage = calculate_damage(friend['strength'])
    exp_info = get_experience_progress(friend['user_id'])
    status_emoji = get_player_status_emoji(friend)
    league = get_league_label(friend.get('rating_points', 0))
    # Кнопка "пригласить в рейд": только если viewer не занят co-op парой и нет уже
    # активного приглашения именно этому другу
    can_invite = (
        viewer_id is not None
        and viewer_id != friend['user_id']
        and viewer_id not in coop_raid_pairs
        and friend['user_id'] not in coop_raid_invites
    )
    profile_text = format_profile_text(
        nickname=friend["nickname"],
        status=f"{status_emoji} {friend['status']}",
        level=friend["player_level"],
        current_exp=exp_info["current_exp"],
        needed_exp=exp_info["needed_exp"],
        rating_points=friend.get("rating_points", 0),
        league=league,
        wins=friend["wins"],
        strength=int(friend["strength"]),
        health=health,
        coins=friend["coins"],
        crystals=friend["crystals"],
        raid_tickets=friend["raid_tickets"],
        likes=friend.get("likes", 0),
    )
    await send_image_with_text(message, "images/profile.png", profile_text,
                               reply_markup=get_friend_profile_kb(can_invite_raid=can_invite, viewer_id=viewer_id, friend_id=friend['user_id']))

@router.message(FriendsMenu.viewing_friend_profile)
async def handle_friend_profile(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅️ Назад в друзья":
        await state.set_state(FriendsMenu.viewing_friends)
        data = await state.get_data()
        page = data.get('friends_page', 0)
        await _send_friends_list(message, state, user_id, page)
        return

    if text == "❌ Удалить из друзей":
        data = await state.get_data()
        friend_id = data.get('viewing_friend_id')
        if friend_id:
            remove_friend(user_id, friend_id)
            await message.answer("✅ Друг удалён!")
        await state.set_state(FriendsMenu.viewing_friends)
        page = data.get('friends_page', 0)
        await _send_friends_list(message, state, user_id, page)
        return

    if text == "⚔️ Пригласить в рейд":
        data = await state.get_data()
        friend_id = data.get('viewing_friend_id')
        if not friend_id:
            await message.answer(f"{E_CROSS} Не удалось определить друга.", reply_markup=get_main_kb())
            await state.clear()
            return
        player = get_player(user_id)
        if not player:
            await message.answer("Сначала зарегистрируйся! /start")
            return
        # Проверки перед отправкой приглашения
        if user_id in coop_raid_pairs:
            await message.answer(f"{E_CROSS} Ты уже в co-op паре! Сначала завершите текущий совместный рейд.")
            return
        if friend_id in coop_raid_invites:
            await message.answer(f"{E_CROSS} Этому игроку уже отправлено приглашение, подожди ответа.")
            return
        friend = get_player(friend_id)
        if not friend:
            await message.answer(f"{E_CROSS} Игрок не найден.")
            return
        # Сохраняем приглашение (nickname хранится raw, эскейп при отображении)
        coop_raid_invites[friend_id] = {
            'inviter_id': user_id,
            'inviter_nickname': player['nickname'],
            'inviter_chat_id': message.chat.id,
        }
        # Устанавливаем состояние приглашённому
        friend_state = dp.fsm.resolve_context(bot, friend_id, friend_id)
        await friend_state.set_state(CoopRaidState.waiting_invite)
        await friend_state.update_data(coop_inviter_id=user_id)
        invite_text = (
            f'{E_SWORD} <b>ПРИГЛАШЕНИЕ В CO-OP РЕЙД</b>\n\n'
            f'{E_CROWN} {html.escape(player["nickname"])} приглашает тебя '
            f'в совместный рейд!\n\n'
            f'{E_SQ}{E_ATK} Сила организатора: {int(player["strength"])}\n'
            f'{E_SQ}{E_HP} HP: {calculate_player_health(player["strength"])}\n\n'
            f'Принять или отклонить?'
        )
        try:
            await bot.send_message(
                chat_id=friend_id,
                text=invite_text,
                reply_markup=get_coop_invite_kb(),
                parse_mode="HTML"
            )
        except Exception:
            coop_raid_invites.pop(friend_id, None)
            await friend_state.clear()
            await message.answer(f"{E_CROSS} Не удалось отправить приглашение игроку.")
            return
        await message.answer(
            f'{E_CHECK} Приглашение отправлено {html.escape(friend["nickname"])}!\n'
            f'{E_HOURGLASS} Ожидаем ответа...',
        )
        return

    if text in ("❤️ Лайк", "❤️ Лайкнуто"):
        data = await state.get_data()
        friend_id = data.get('viewing_friend_id')
        if text == "❤️ Лайкнуто" or (friend_id and has_liked_player(user_id, friend_id)):
            await message.answer("❤️ Вы уже ставили лайк этому игроку!")
            return
        if friend_id:
            # Enter послание state
            await state.set_state(LikeState.waiting_message_from_friend)
            await state.update_data(like_target_id=friend_id)
            cancel_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)
            await message.answer(
                f"{E_HP} Напишите послание для этого игрока:\n(оно будет отправлено вместе с лайком)",
                reply_markup=cancel_kb
            )
        return

    # fallback — перерисовать профиль
    data = await state.get_data()
    friend_id = data.get('viewing_friend_id')
    if friend_id:
        friend = get_player(friend_id)
        if friend:
            await _send_friend_profile(message, friend, viewer_id=user_id)
            return
    await state.set_state(FriendsMenu.viewing_friends)
    data = await state.get_data()
    page = data.get('friends_page', 0)
    await _send_friends_list(message, state, user_id, page)

@router.message(LikeState.waiting_message_from_friend)
async def process_like_message_from_friend(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text or ""
    data = await state.get_data()
    target_id = data.get('like_target_id')
    friends_page = data.get('friends_page', 0)

    if text == "❌ Отмена":
        await state.set_state(FriendsMenu.viewing_friend_profile)
        target_player = get_player(target_id) if target_id else None
        if target_player:
            await _send_friend_profile(message, target_player, viewer_id=user_id)
        else:
            await state.set_state(FriendsMenu.viewing_friends)
            await _send_friends_list(message, state, user_id, friends_page)
        return

    if not target_id:
        await state.set_state(FriendsMenu.viewing_friends)
        await message.answer(f"{E_CROSS} Ошибка: игрок не найден.")
        await _send_friends_list(message, state, user_id, friends_page)
        return

    poslanie = text.strip()[:200]  # limit message length
    result = give_like_to_player(user_id, target_id, poslanie)
    await state.set_state(FriendsMenu.viewing_friend_profile)
    if result:
        liker = get_player(user_id)
        if liker:
            safe_liker_nick = html.escape(liker['nickname'])
            safe_poslanie = html.escape(poslanie)
            try:
                await bot.send_message(
                    chat_id=target_id,
                    text=f"{E_HP} ваш профиль оценил {safe_liker_nick}!\n{safe_poslanie}",
                    parse_mode="HTML"
                )
            except Exception:
                pass
        await message.answer(f"❤️ Лайк и послание отправлены!")
    else:
        await message.answer("❤️ Вы уже ставили лайк этому игроку!")
    # Refresh friend profile
    target_player = get_player(target_id)
    if target_player:
        await _send_friend_profile(message, target_player, viewer_id=user_id)


    """Показать заявки в друзья"""
    request_ids = get_friend_requests(user_id)

    if not request_ids:
        text = '<tg-emoji emoji-id="5206510891247371052">🔽</tg-emoji> 🔽 У вас нет новых заявок в друзья!'
        kb = [[KeyboardButton(text="⬅️ Назад в друзья")]]
        await message.answer(text, reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), parse_mode="HTML")
        return

    requests_data = []
    for rid in request_ids:
        rp = get_player(rid)
        if rp:
            requests_data.append(rp)

    text = f'<tg-emoji emoji-id="5206510891247371052">🔽</tg-emoji> 🔽 Заявки в друзья: {len(requests_data)}\n\n'
    for req in requests_data:
        safe_nick = html.escape(req['nickname'])
        text += (
            f'{E_SQ}{E_RARITY_ULTRA} {safe_nick}\n'
            f'  ├ Сила: {int(req["strength"])} {E_ATK}\n\n'
        )

    await message.answer(text, reply_markup=get_friend_requests_kb(requests_data), parse_mode="HTML")

@router.message(FriendsMenu.viewing_requests)
async def handle_friend_requests(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅️ Назад в друзья":
        await state.set_state(FriendsMenu.viewing_friends)
        data = await state.get_data()
        page = data.get('friends_page', 0)
        await _send_friends_list(message, state, user_id, page)
        return

    if text and text.startswith("✅ Принять: "):
        nickname = text[len("✅ Принять: "):]
        target = get_player_by_nickname(nickname)
        if target:
            accepted = accept_friend_request(user_id, target['user_id'])
            if accepted:
                await message.answer(f"✅ Вы приняли {html.escape(nickname)} в друзья!", parse_mode="HTML")
            else:
                await message.answer("❌ Заявка не найдена.")
        else:
            await message.answer("❌ Игрок не найден.")
        await _send_friend_requests(message, user_id)
        return

    if text and text.startswith("❌ Отклонить: "):
        nickname = text[len("❌ Отклонить: "):]
        target = get_player_by_nickname(nickname)
        if target:
            declined = decline_friend_request(user_id, target['user_id'])
            if declined:
                await message.answer(f"❌ Заявка от {html.escape(nickname)} отклонена.", parse_mode="HTML")
            else:
                await message.answer("❌ Заявка не найдена.")
        else:
            await message.answer("❌ Игрок не найден.")
        await _send_friend_requests(message, user_id)
        return

    await _send_friend_requests(message, user_id)

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


def _fmt_player_stats(nickname: str, health, damage, mana) -> str:
    """Блок статов игрока для боевого UI"""
    return (
        f"{E_PROFILE} {nickname}\n"
        f"{E_SQ}{E_HP} {health} {E_YELLOW}\n"
        f"{E_SQ}{E_ATK} {damage} {E_YELLOW}\n"
        f"{E_SQ}{E_MANA} Мана: {mana}/100 {E_BOOK_MANA}"
    )


def _fmt_enemy_stats(name: str, health, damage) -> str:
    """Блок статов врага для боевого UI"""
    return (
        f"{E_SKULL} {name}\n"
        f"{E_SQ}{E_ESWORD} {health} {E_RED_C}\n"
        f"{E_SQ}{E_ATK} {damage} {E_RED_C}"
    )


def _fmt_victory(enemy_name: str, reward_lines: list[str]) -> str:
    """Текст победы"""
    return (
        f"{E_CHART} Результаты боя:\n\n"
        f"{E_SKULL} {enemy_name} повержен! {E_TRASH}\n\n"
        f"{E_TROPHY}{E_GREEN} ВЫ ПОБЕДИЛИ!\n\n"
        f"{E_GIFT} Получено:\n" + "\n".join(reward_lines) + "\n"
    )


def _fmt_defeat(nickname: str, enemy_name: str, is_location: bool = False) -> str:
    """Текст поражения"""
    text = (
        f"{E_CHART} Результаты боя:\n\n"
        f"{E_PROFILE} {nickname} повержен! {E_ARROW_DN}\n\n"
        f"{E_BOOK_LOSS}{E_RED_C} ВЫ ПРОИГРАЛИ!\n\n"
        f"{E_SKULL}{E_RED_C} Ты был повержен {enemy_name}..."
    )
    if not is_location:
        text += f"\n\n{E_BAN} Потеряно:\n{E_CROSS} 10 💠 очков рейтинга"
    return text

@router.message(F.text == "🐉 Рейд")
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

    has_coop = user_id in coop_raid_pairs
    coop_info = ""
    if has_coop:
        partner_id = coop_raid_pairs[user_id]
        partner = get_player(partner_id)
        p_nick = html.escape(partner['nickname']) if partner else "Партнёр"
        coop_info = f'\n{E_SWORD} Партнёр готов: {p_nick} — нажми <b>🤝 Начать совместный рейд</b>!'

    raid_menu_text = (
        f'<tg-emoji emoji-id="5201888948091129713">🔗</tg-emoji> | Меню рейда {html.escape(player["nickname"])}:\n'
        f'<tg-emoji emoji-id="5357471466919056181">🔘</tg-emoji> Рекорд этажа: {player["raid_max_floor"]} <tg-emoji emoji-id="5359669309058603132">🏆</tg-emoji>'
        f'{coop_info}'
    )
    await state.set_state(RaidState.viewing_menu)
    await send_image_with_text(message, "images/raid.png", raid_menu_text,
                               reply_markup=get_raid_menu_kb(has_coop_partner=has_coop))


@router.message(RaidState.viewing_menu)
async def handle_raid_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "❌ Выйти":
        # Если уходим из меню рейда — разрываем co-op пару (если была)
        if user_id in coop_raid_pairs:
            partner_id = coop_raid_pairs.pop(user_id)
            coop_raid_pairs.pop(partner_id, None)
            try:
                await bot.send_message(
                    chat_id=partner_id,
                    text=f"{E_CROSS} Партнёр покинул меню рейда. Совместный рейд отменён.",
                    reply_markup=get_main_kb(),
                    parse_mode="HTML"
                )
                partner_state = dp.fsm.resolve_context(bot, partner_id, partner_id)
                await partner_state.clear()
            except Exception:
                pass
        await show_main_menu(message, state)
        return

    # ============ CO-OP старт ============
    if text == "🤝 Начать совместный рейд":
        if user_id not in coop_raid_pairs:
            await message.answer(
                f"{E_CROSS} У тебя нет партнёра для совместного рейда!",
                reply_markup=get_raid_menu_kb(has_coop_partner=False)
            )
            return

        partner_id = coop_raid_pairs[user_id]
        player = get_player(user_id)
        partner = get_player(partner_id)

        if not player or not partner:
            coop_raid_pairs.pop(user_id, None)
            coop_raid_pairs.pop(partner_id, None)
            await message.answer(f"{E_CROSS} Ошибка: игрок не найден.", reply_markup=get_main_kb())
            await state.clear()
            return

        # Проверяем билеты
        if player['raid_tickets'] <= 0:
            await message.answer(
                f"{E_TICKET} У тебя нет билетов рейда!\nКупи билеты на рынке.",
                reply_markup=get_raid_menu_kb(has_coop_partner=True)
            )
            return
        if partner['raid_tickets'] <= 0:
            await message.answer(
                f"{E_TICKET} У партнёра нет билетов рейда! Рейд невозможен.",
                reply_markup=get_raid_menu_kb(has_coop_partner=True)
            )
            return

        # Проверяем что партнёр в лобби
        partner_state = dp.fsm.resolve_context(bot, partner_id, partner_id)
        current_partner_state = await partner_state.get_state()
        if current_partner_state != CoopRaidState.in_lobby:
            coop_raid_pairs.pop(user_id, None)
            coop_raid_pairs.pop(partner_id, None)
            await message.answer(
                f"{E_CROSS} Партнёр покинул лобби. Совместный рейд отменён.",
                reply_markup=get_raid_menu_kb(has_coop_partner=False)
            )
            return

        # Всё ок — удаляем из пар и стартуем
        coop_raid_pairs.pop(user_id, None)
        coop_raid_pairs.pop(partner_id, None)

        remove_raid_ticket(user_id)
        remove_raid_ticket(partner_id)

        # Характеристики обоих игроков с баффом клана
        p1_clan = get_player_clan(user_id)
        p1_clan_lvl = p1_clan['clan_level'] if p1_clan else 1
        p1_str = apply_clan_strength_buff(player['strength'], p1_clan_lvl)
        p1_hp = calculate_player_health(p1_str)
        p1_dmg = calculate_damage(p1_str)

        p2_clan = get_player_clan(partner_id)
        p2_clan_lvl = p2_clan['clan_level'] if p2_clan else 1
        p2_str = apply_clan_strength_buff(partner['strength'], p2_clan_lvl)
        p2_hp = calculate_player_health(p2_str)
        p2_dmg = calculate_damage(p2_str)

        floor_id = 1
        enemy_info = RAID_FLOORS[floor_id]
        coop_enemy_hp = int(enemy_info['health'] * _COOP_ENEMY_HP_MULT)
        enemy_dmg = enemy_info['base_damage']
        mana = 100

        p1_goes_first = random.random() < 0.5
        p1_nick = html.escape(player['nickname'])
        p2_nick = html.escape(partner['nickname'])

        common = {
            'coop_floor': floor_id,
            'coop_enemy_health': coop_enemy_hp,
            'coop_enemy_base_damage': enemy_dmg,
            'coop_enemy_skip_turn': False,
        }
        await state.update_data(
            **common,
            coop_partner_id=partner_id,
            coop_my_health=p1_hp,
            coop_my_damage=p1_dmg,
            coop_my_mana=mana,
            coop_is_my_turn=p1_goes_first,
            coop_my_blind_turns=0,
            coop_partner_health=p2_hp,
            coop_partner_nickname=p2_nick,
        )
        await state.set_state(CoopRaidState.in_raid)

        await partner_state.update_data(
            **common,
            coop_partner_id=user_id,
            coop_my_health=p2_hp,
            coop_my_damage=p2_dmg,
            coop_my_mana=mana,
            coop_is_my_turn=not p1_goes_first,
            coop_my_blind_turns=0,
            coop_partner_health=p1_hp,
            coop_partner_nickname=p1_nick,
        )
        await partner_state.set_state(CoopRaidState.in_raid)

        reset_battle_cooldown(user_id)
        reset_battle_cooldown(partner_id)

        first_nick = p1_nick if p1_goes_first else p2_nick
        start_header = (
            f"{E_SWORD} <b>CO-OP РЕЙД НАЧАЛСЯ!</b>\n\n"
            f"{E_HASHTAG} Первым ходит: {first_nick}\n\n"
        )
        floor_block = _fmt_coop_floor_info(floor_id, enemy_info, coop_enemy_hp)
        p1_stats = _fmt_coop_stats(p1_nick, p1_hp, p1_dmg, mana, p2_nick, p2_hp,
                                   enemy_info['name'], enemy_info['emoji'], coop_enemy_hp, enemy_dmg)
        full_start = start_header + floor_block + "\n" + p1_stats

        if p1_goes_first:
            await message.answer(full_start + f"\n\n{E_SWORD} Твой ход!", reply_markup=get_battle_action_kb(user_id, mana))
            try:
                await bot.send_message(
                    chat_id=partner_id,
                    text=full_start + f"\n\n{E_HOURGLASS} Ход партнёра...",
                    reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True),
                    parse_mode="HTML"
                )
            except Exception:
                pass
        else:
            await message.answer(full_start + f"\n\n{E_HOURGLASS} Ход партнёра...",
                                 reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
            try:
                await bot.send_message(
                    chat_id=partner_id,
                    text=full_start + f"\n\n{E_SWORD} Твой ход!",
                    reply_markup=get_battle_action_kb(partner_id, mana),
                    parse_mode="HTML"
                )
            except Exception:
                pass
        return

    # ============ SOLO старт ============
    if text != "⚔️ Начать рейд":
        has_coop = user_id in coop_raid_pairs
        await message.answer("Выбери действие!", reply_markup=get_raid_menu_kb(has_coop_partner=has_coop))
        return

    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    # Если был co-op партнёр — разрываем пару (игрок сам выбрал соло)
    if user_id in coop_raid_pairs:
        partner_id = coop_raid_pairs.pop(user_id)
        coop_raid_pairs.pop(partner_id, None)
        try:
            await bot.send_message(
                chat_id=partner_id,
                text=f"{E_CROSS} Партнёр начал соло рейд. Совместный рейд отменён.",
                reply_markup=get_main_kb(),
                parse_mode="HTML"
            )
            partner_state = dp.fsm.resolve_context(bot, partner_id, partner_id)
            await partner_state.clear()
        except Exception:
            pass

    # Проверить наличие билета рейда (повторная проверка)
    if player['raid_tickets'] <= 0:
        await state.clear()
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
        f"{_fmt_player_stats(html.escape(player['nickname']), player_health, player_damage, mana)}\n\n"
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
        raid_text += (
            f"\n\n{E_HASHTAG} Сейчас твой ход!\n"
            f"{E_SQ} ты ходишь первым:"
        )
        await message.answer(raid_text, reply_markup=get_battle_action_kb(user_id, mana))
    else:
        await message.answer(raid_text + f"\n\n{E_WARN} Враг ходит первым!",
                               reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await asyncio.sleep(2)

        enemy_hit = int(round(enemy_damage * random.uniform(0.7, 1.3)))
        new_player_health = player_health - enemy_hit

        log = (
            f"🐉 <b>РЕЙД — Этаж {floor_id}/10</b>\n\n"
            f"{E_SKULL} {enemy_info['name']} атакует! {E_ARROW_DN}\n"
            f"{E_DMG}{E_HEART_B} Урон тебе: {enemy_hit}\n\n"
        )

        if new_player_health <= 0:
            update_player_raid_floor(user_id, 0)
            update_rating_points(user_id, -10)
            increment_player_deaths(user_id)
            log += _fmt_defeat(html.escape(player['nickname']), enemy_info['name'])
            log += f"\n\nРекорд: {player['raid_max_floor']} этаж."
            await message.answer(log, reply_markup=get_end_battle_kb())
            await state.clear()
            return

        log += (
            f"{_fmt_player_stats(html.escape(player['nickname']), new_player_health, player_damage, mana)}\n\n"
            f"{_fmt_enemy_stats(enemy_info['name'], enemy_info['health'], enemy_damage)}"
        )
        await state.update_data(player_health=new_player_health)
        await message.answer(log, reply_markup=get_battle_action_kb(user_id, mana))


@router.message(RaidState.in_raid)
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
            await show_main_menu(message, state)
            return
        await message.answer("Выбери действие!", reply_markup=get_battle_action_kb(user_id, mana))
        return

    # Проверка cooldown (2 сек)
    if not can_battle_action(user_id):
        await message.answer("⏳ Подожди перед следующим ходом!")
        return

    log = f"🐉 <b>РЕЙД — Этаж {floor_id}/10</b>\n\n"
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
                f"{E_CROSS} Недостаточно маны! Требуется {sk['mana_cost']}{E_MANA}",
                reply_markup=get_battle_action_kb(user_id, mana)
            )
            return
        new_mana -= sk['mana_cost']
        log += f"✨ {sk['name']}!\n"

        # 10% базовый промах
        if roll_miss():
            increment_player_dodges(user_id)
            log += f"{E_CROSS}{E_ATK} Промах! Враг уклонился\n\n"
            player_hit = 0
        elif sk_id == 1:  # Мега-молот: 70% урон + стан
            player_hit = int(round(data['player_damage'] * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            log += f"{E_PROFILE} {html.escape(player['nickname'])} наносит {player_hit} урона! {E_ARROW_UP}\n"
            if random.random() < sk['stun_chance']:
                new_enemy_skip = True
                log += "😵 Враг оглушён и пропустит следующий ход!\n"
        elif sk_id == 2:  # Кровавое неистовство: 2x урон, -15% HP
            player_hit = int(round(data['player_damage'] * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            hp_loss = max(1, int(round(calculate_player_health(player['strength']) * sk['hp_loss_pct'])))
            new_player_health = max(1, new_player_health - hp_loss)
            log += f"🩸 Вы теряете {hp_loss} HP!\n"
            log += f"{E_PROFILE} {html.escape(player['nickname'])} наносит {player_hit} урона! {E_ARROW_UP}\n"
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
            increment_player_dodges(user_id)
            log += (
                f"{E_CROSS}{E_ATK} Ты промахиваешься!\n"
                f"{E_SQ}Неудачный крит шанс.\n\n"
            )
            # Враг атакует без ответа
            if enemy_skip_turn:
                log += f"😵 {enemy_info['name']} оглушён, пропускает ход!\n\n"
                log += (
                    f"{_fmt_player_stats(html.escape(player['nickname']), new_player_health, data['player_damage'], new_mana)}\n\n"
                    f"{_fmt_enemy_stats(enemy_info['name'], new_enemy_health, data['enemy_damage'])}"
                )
                await message.answer(log, reply_markup=get_battle_action_kb(user_id, new_mana))
                await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health,
                                        player_mana=new_mana, enemy_skip_turn=False, player_blind_turns=new_player_blind)
                return
            enemy_hit = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
            new_player_health = int(round(new_player_health - enemy_hit))
            log += (
                f"{E_SKULL} {enemy_info['name']} атакует тебя! {E_ARROW_DN}\n"
                f"{E_DMG}{E_HEART_B} Урон тебе: {enemy_hit}\n\n"
            )
            if new_player_health <= 0:
                floors_completed = floor_id - 1
                new_max = max(player['raid_max_floor'], floors_completed)
                if new_max > player['raid_max_floor']:
                    update_player_raid_max_floor(user_id, new_max)
                update_player_raid_floor(user_id, 0)
                update_rating_points(user_id, -10)
                increment_player_deaths(user_id)
                log += _fmt_defeat(html.escape(player['nickname']), enemy_info['name'])
                log += f"\n\nПройдено этажей: {floors_completed}. Рекорд: {new_max}."
                await message.answer(log, reply_markup=get_end_battle_kb())
                await state.clear()
                return
            log += (
                f"{_fmt_player_stats(html.escape(player['nickname']), new_player_health, data['player_damage'], new_mana)}\n\n"
                f"{_fmt_enemy_stats(enemy_info['name'], new_enemy_health, data['enemy_damage'])}"
            )
            await message.answer(log, reply_markup=get_battle_action_kb(user_id, new_mana))
            await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health,
                                    player_mana=new_mana, enemy_skip_turn=new_enemy_skip, player_blind_turns=new_player_blind)
            return
        # Крит успешный
        if roll_miss():
            player_hit = 0
            increment_player_dodges(user_id)
            log += f"{E_CROSS}{E_ATK} Промах! Враг уклонился\n\n"
        else:
            base_dmg = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
            player_hit = base_dmg * 2
            log += f"{E_DMG} КРИТИЧЕСКИЙ УДАР! {E_ARROW_UP}\n{E_PROFILE} {html.escape(player['nickname'])} атакует!\n{E_DMG}{E_ESWORD} Урон врагу: {player_hit}\n\n"
    else:
        # Обычная атака
        if roll_miss():
            player_hit = 0
            increment_player_dodges(user_id)
            log += f"{E_CROSS}{E_ATK} Промах! Враг уклонился\n\n"
        else:
            player_hit = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
            log += (
                f"{E_BELL}{E_DMG} Ты ударяешь! \n\n"
                f"{E_PROFILE} {html.escape(player['nickname'])} атакует! {E_ARROW_UP}\n"
                f"{E_DMG}{E_ESWORD} Урон врагу: {player_hit}\n\n"
            )

    new_enemy_health = int(round(new_enemy_health - player_hit))

    if new_enemy_health <= 0:
        # Победа на этаже
        reward = enemy_info['reward']
        add_coins_to_player(user_id, reward)
        update_rating_points(user_id, 5)
        increment_player_pve_wins(user_id)
        if floor_id > player['raid_max_floor']:
            update_player_raid_max_floor(user_id, floor_id)
        player_clan = get_player_clan(user_id)
        if player_clan:
            add_clan_exp(player_clan['clan_id'], 10)

        reward_lines = [
            f"{E_PLUS} {reward} {E_COINS} монет",
            f"{E_PLUS} 5 💠 очков рейтинга",
        ]
        if player_clan:
            reward_lines.append(f"{E_PLUS} 10 опыта клану")

        log += _fmt_victory(f"{enemy_info['emoji']} {enemy_info['name']}", reward_lines)
        log += f"\n{E_TROPHY} <b>ЭТАЖ {floor_id} ПРОЙДЕН!</b>\n"

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
                f"{_fmt_player_stats(html.escape(player_refreshed['nickname']), new_p_health, new_p_damage, next_mana)}"
            )
            await message.answer(next_text, reply_markup=get_battle_action_kb(user_id, next_mana))
        return

    # Враг контратакует
    if enemy_skip_turn:
        log += f"😵 {enemy_info['name']} оглушён, пропускает ход!\n\n"
        enemy_hit = 0
    else:
        # Применяем ослепление если активно
        blind_extra = SKILLS[3]['miss_chance_add'] if new_player_blind > 0 else 0.0
        if roll_miss(blind_extra):
            enemy_hit = 0
            increment_player_dodges(user_id)
            log += f"{E_CROSS}{E_ATK} {enemy_info['name']} промахивается!\n\n"
        else:
            enemy_hit = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
            new_player_health = int(round(new_player_health - enemy_hit))
            log += (
                f"{E_SKULL} {enemy_info['name']} контратакует! {E_ARROW_DN}\n"
                f"{E_DMG}{E_HEART_B} Урон тебе: {enemy_hit}\n\n"
            )

    if new_player_health <= 0:
        floors_completed = floor_id - 1
        new_max = max(player['raid_max_floor'], floors_completed)
        if new_max > player['raid_max_floor']:
            update_player_raid_max_floor(user_id, new_max)
        update_player_raid_floor(user_id, 0)
        update_rating_points(user_id, -10)
        increment_player_deaths(user_id)
        log += _fmt_defeat(html.escape(player['nickname']), enemy_info['name'])
        log += f"\n\nПройдено этажей: {floors_completed}. Рекорд: {new_max}."
        await message.answer(log, reply_markup=get_end_battle_kb())
        await state.clear()
        return

    log += (
        f"\n{_fmt_player_stats(html.escape(player['nickname']), new_player_health, data['player_damage'], new_mana)}\n\n"
        f"{_fmt_enemy_stats(enemy_info['name'], new_enemy_health, data['enemy_damage'])}"
    )
    await message.answer(log, reply_markup=get_battle_action_kb(user_id, new_mana))
    await state.update_data(
        player_health=new_player_health,
        enemy_health=new_enemy_health,
        player_mana=new_mana,
        enemy_skip_turn=new_enemy_skip,
        player_blind_turns=new_player_blind,
    )


# ============== CO-OP RAID ==============
# Множители CO-OP (враг сильнее, но и награда выше)
_COOP_ENEMY_HP_MULT  = 1.5   # HP врага в co-op × 1.5
_COOP_REWARD_MULT    = 1.25  # Монеты за этаж × 1.25


def _fmt_coop_floor_info(floor_id: int, enemy_info: dict, coop_hp: int) -> str:
    """Блок информации об этаже для CO-OP"""
    return (
        f"{E_SKULL} {enemy_info['emoji']} <b>{enemy_info['name']}</b>\n"
        f"{E_SQ}{E_ESWORD} {coop_hp} {E_RED_C}  "
        f"{E_SQ}{E_ATK} {enemy_info['base_damage']} {E_RED_C}\n"
        f"{E_SQ}{E_COINS} Награда: {int(enemy_info['reward'] * _COOP_REWARD_MULT)} (каждому)\n"
    )


def _fmt_coop_stats(
    my_nick: str, my_hp: int, my_dmg: int, my_mana: int,
    par_nick: str, par_hp: int,
    e_name: str, e_emoji: str, e_hp: int, e_dmg: int,
) -> str:
    """Блок статов обоих игроков и врага для CO-OP"""
    return (
        f"{E_CROWN} {my_nick}\n"
        f"{E_SQ}{E_HP} {my_hp}  {E_SQ}{E_ATK} {my_dmg}  {E_SQ}{E_MANA} {my_mana}/100\n\n"
        f"{E_PROFILE} {par_nick}\n"
        f"{E_SQ}{E_HP} {par_hp}\n\n"
        f"{E_SKULL} {e_emoji} {e_name}\n"
        f"{E_SQ}{E_ESWORD} {e_hp} {E_RED_C}  {E_SQ}{E_ATK} {e_dmg} {E_RED_C}"
    )


async def _coop_pass_turn(
    my_id: int, partner_id: int,
    my_state: FSMContext, message,
    log: str,
    new_my_hp: int, new_enemy_hp: int, new_mana: int,
    new_enemy_skip: bool, new_my_blind: int,
    partner_health: int, partner_nickname: str,
    floor_id: int,
):
    """Сохранить состояние и передать ход партнёру."""
    await my_state.update_data(
        coop_my_health=new_my_hp,
        coop_enemy_health=new_enemy_hp,
        coop_my_mana=new_mana,
        coop_is_my_turn=False,
        coop_enemy_skip_turn=new_enemy_skip,
        coop_my_blind_turns=new_my_blind,
    )
    await message.answer(
        log + f"\n\n{E_HOURGLASS} Ход партнёра...",
        reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True),
    )

    partner_state = dp.fsm.resolve_context(bot, partner_id, partner_id)
    partner_data = await partner_state.get_data()
    par_mana   = partner_data.get('coop_my_mana', 100)
    par_dmg    = partner_data.get('coop_my_damage', 0)
    par_hp_cur = partner_data.get('coop_my_health', 0)

    # Синхронизируем HP врага и моё актуальное HP (как partner_health для партнёра)
    await partner_state.update_data(
        coop_enemy_health=new_enemy_hp,
        coop_is_my_turn=True,
        coop_partner_health=new_my_hp,
    )

    enemy_info = RAID_FLOORS[floor_id]
    partner_log = (
        f"{E_DOT} Партнёр ходил:\n{log}\n\n"
        + _fmt_coop_stats(
            partner_nickname, par_hp_cur, par_dmg, par_mana,
            partner_data.get('coop_partner_nickname', 'Партнёр'), new_my_hp,
            enemy_info['name'], enemy_info['emoji'], new_enemy_hp, enemy_info['base_damage'],
        )
        + f"\n\n{E_SWORD} Твой ход!"
    )
    try:
        await bot.send_message(
            chat_id=partner_id,
            text=partner_log,
            reply_markup=get_battle_action_kb(partner_id, par_mana),
            parse_mode="HTML",
        )
    except Exception:
        pass


async def _coop_floor_victory(
    my_id: int, partner_id: int,
    my_state: FSMContext, message,
    floor_id: int, player: dict,
):
    """Победа на этаже CO-OP рейда — наградить обоих, перейти на следующий или завершить."""
    enemy_info   = RAID_FLOORS[floor_id]
    reward_coins = int(round(enemy_info['reward'] * _COOP_REWARD_MULT))
    my_data      = await my_state.get_data()
    par_nick     = my_data.get('coop_partner_nickname', 'Партнёр')
    my_nick      = html.escape(player['nickname'])

    # Награды каждому
    for uid in (my_id, partner_id):
        add_coins_to_player(uid, reward_coins)
        increment_player_pve_wins(uid)
        update_rating_points(uid, 5)
        p = get_player(uid)
        if p and floor_id > p.get('raid_max_floor', 0):
            update_player_raid_max_floor(uid, floor_id)

    # Клановый опыт
    my_clan = get_player_clan(my_id)
    if my_clan:
        add_clan_exp(my_clan['clan_id'], 15)

    victory_text = (
        f"{E_CHART} Этаж {floor_id} пройден!\n\n"
        f"{E_SKULL} {enemy_info['emoji']} {enemy_info['name']} повержен! {E_TRASH}\n\n"
        f"{E_TROPHY}{E_GREEN} <b>CO-OP ПОБЕДА!</b>\n\n"
        f"{E_PROFILE} {my_nick} {E_CHECK}\n"
        f"{E_PROFILE} {par_nick} {E_CHECK}\n\n"
        f"{E_GIFT} Каждый получил:\n"
        f"{E_PLUS} {reward_coins} {E_COINS} монет\n"
        f"{E_PLUS} 5 {E_STAR} рейтинга\n"
        f"{E_PLUS} 15 {E_CLAN_BOTTLE} опыта клана\n"
    )

    if floor_id == 10:
        victory_text += (
            "\n🎉 <b>ПОЗДРАВЛЯЕМ!</b>\n"
            "Вы вместе прошли все 10 этажей!\n"
            f"{E_SKULL} Зеркальный дух повержён!\n\n"
            "Совместный рейд завершён."
        )
        await message.answer(victory_text, reply_markup=get_end_battle_kb())
        await my_state.clear()
        partner_state = dp.fsm.resolve_context(bot, partner_id, partner_id)
        await partner_state.clear()
        try:
            await bot.send_message(
                chat_id=partner_id, text=victory_text,
                reply_markup=get_end_battle_kb(), parse_mode="HTML",
            )
        except Exception:
            pass
        return

    # Переход на следующий этаж
    next_floor    = floor_id + 1
    next_enemy    = RAID_FLOORS[next_floor]
    coop_enemy_hp = int(next_enemy['health'] * _COOP_ENEMY_HP_MULT)

    partner_state = dp.fsm.resolve_context(bot, partner_id, partner_id)
    partner_data  = await partner_state.get_data()
    partner       = get_player(partner_id)

    new_my_hp  = calculate_player_health(apply_clan_strength_buff(
        player['strength'], get_player_clan(my_id)['clan_level'] if get_player_clan(my_id) else 1))
    new_my_dmg = calculate_damage(apply_clan_strength_buff(
        player['strength'], get_player_clan(my_id)['clan_level'] if get_player_clan(my_id) else 1))
    if partner:
        p2_clan_lvl = get_player_clan(partner_id)['clan_level'] if get_player_clan(partner_id) else 1
        new_par_hp  = calculate_player_health(apply_clan_strength_buff(partner['strength'], p2_clan_lvl))
        new_par_dmg = calculate_damage(apply_clan_strength_buff(partner['strength'], p2_clan_lvl))
    else:
        new_par_hp  = partner_data.get('coop_my_health', 0)
        new_par_dmg = partner_data.get('coop_my_damage', 0)
    new_mana   = 100

    i_go_first = random.random() < 0.5
    common = {
        'coop_floor': next_floor,
        'coop_enemy_health': coop_enemy_hp,
        'coop_enemy_base_damage': next_enemy['base_damage'],
        'coop_enemy_skip_turn': False,
    }
    await my_state.update_data(
        **common,
        coop_my_health=new_my_hp,
        coop_my_damage=new_my_dmg,
        coop_my_mana=new_mana,
        coop_is_my_turn=i_go_first,
        coop_my_blind_turns=0,
        coop_partner_health=new_par_hp,
    )
    await partner_state.update_data(
        **common,
        coop_my_health=new_par_hp,
        coop_my_damage=new_par_dmg,
        coop_my_mana=new_mana,
        coop_is_my_turn=not i_go_first,
        coop_my_blind_turns=0,
        coop_partner_health=new_my_hp,
    )

    victory_text += f"\n{E_ARROW_UP} Переход на этаж {next_floor}..."
    await message.answer(victory_text, reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
    try:
        await bot.send_message(
            chat_id=partner_id, text=victory_text,
            reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True),
            parse_mode="HTML",
        )
    except Exception:
        pass

    await asyncio.sleep(2)
    reset_battle_cooldown(my_id)
    reset_battle_cooldown(partner_id)

    first_nick = my_nick if i_go_first else par_nick
    next_text = (
        f"{E_SWORD} <b>CO-OP РЕЙД — Этаж {next_floor}/10</b>\n\n"
        f"Первым ходит: {first_nick}\n\n"
        + _fmt_coop_floor_info(next_floor, next_enemy, coop_enemy_hp) + "\n"
        + _fmt_coop_stats(my_nick, new_my_hp, new_my_dmg, new_mana,
                          par_nick, new_par_hp,
                          next_enemy['name'], next_enemy['emoji'],
                          coop_enemy_hp, next_enemy['base_damage'])
    )
    if i_go_first:
        await message.answer(next_text + f"\n\n{E_SWORD} Твой ход!",
                             reply_markup=get_battle_action_kb(my_id, new_mana))
        try:
            await bot.send_message(
                chat_id=partner_id,
                text=next_text + f"\n\n{E_HOURGLASS} Ход партнёра...",
                reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True),
                parse_mode="HTML",
            )
        except Exception:
            pass
    else:
        await message.answer(next_text + f"\n\n{E_HOURGLASS} Ход партнёра...",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        try:
            await bot.send_message(
                chat_id=partner_id,
                text=next_text + f"\n\n{E_SWORD} Твой ход!",
                reply_markup=get_battle_action_kb(partner_id, new_mana),
                parse_mode="HTML",
            )
        except Exception:
            pass


async def _coop_raid_player_died(
    my_id: int, partner_id: int,
    my_state: FSMContext, message,
    floor_id: int, player: dict,
    enemy_info: dict, log: str,
):
    """Один игрок погиб в CO-OP рейде — конец для обоих."""
    floors_done = floor_id - 1
    my_nick = html.escape(player['nickname'])
    my_data = await my_state.get_data()
    par_nick = my_data.get('coop_partner_nickname', 'Партнёр')

    for uid, pts in ((my_id, -10), (partner_id, -5)):
        p = get_player(uid)
        if p:
            new_max = max(p.get('raid_max_floor', 0), floors_done)
            if new_max > p.get('raid_max_floor', 0):
                update_player_raid_max_floor(uid, new_max)
        update_rating_points(uid, pts)
    increment_player_deaths(my_id)

    defeat_text = (
        log
        + f"\n{E_CHART} Результаты CO-OP боя:\n\n"
        + f"{E_BOOK_LOSS}{E_RED_C} <b>CO-OP РЕЙД ПРОВАЛЕН!</b>\n\n"
        + f"{E_PROFILE} {my_nick} пал! {E_SKULL}\n\n"
        + f"{E_BAN} Потери:\n"
        + f"{E_CROSS} -10 {E_STAR} рейтинга\n"
        + f"{E_CROSS} Пройдено этажей: {floors_done}\n"
    )
    partner_defeat = (
        f"{E_CHART} Результаты CO-OP боя:\n\n"
        f"{E_BOOK_LOSS}{E_RED_C} <b>CO-OP РЕЙД ПРОВАЛЕН!</b>\n\n"
        f"{E_SKULL} {my_nick} был повержён — рейд завершён.\n\n"
        f"{E_BAN} Потери:\n"
        f"{E_CROSS} -5 {E_STAR} рейтинга\n"
        f"{E_CROSS} Пройдено этажей: {floors_done}\n"
    )

    await message.answer(defeat_text, reply_markup=get_end_battle_kb())
    await my_state.clear()

    partner_state = dp.fsm.resolve_context(bot, partner_id, partner_id)
    await partner_state.clear()
    try:
        await bot.send_message(
            chat_id=partner_id, text=partner_defeat,
            reply_markup=get_end_battle_kb(), parse_mode="HTML",
        )
    except Exception:
        pass


async def _coop_raid_forfeit(my_id: int, partner_id, my_state: FSMContext, message):
    """Игрок покинул CO-OP рейд досрочно."""
    player = get_player(my_id)
    my_nick = html.escape(player['nickname']) if player else 'Игрок'
    await my_state.clear()
    await show_main_menu(message, my_state)
    if partner_id:
        partner_state = dp.fsm.resolve_context(bot, partner_id, partner_id)
        await partner_state.clear()
        try:
            await bot.send_message(
                chat_id=partner_id,
                text=(
                    f"{E_CROSS} {my_nick} покинул CO-OP рейд.\n\n"
                    f"{E_BAN} Рейд завершён досрочно."
                ),
                reply_markup=get_end_battle_kb(),
                parse_mode="HTML",
            )
        except Exception:
            pass


# --- Приглашение: принять / отклонить ---
@router.message(CoopRaidState.waiting_invite)
async def handle_coop_invite_response(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text    = message.text

    if text == "✅ Принять рейд":
        invite = coop_raid_invites.pop(user_id, None)
        if not invite:
            await state.clear()
            await message.answer(
                f"{E_WARN} Приглашение уже истекло или было отозвано.",
                reply_markup=get_main_kb(),
            )
            return

        inviter_id       = invite['inviter_id']
        inviter_nickname = invite['inviter_nickname']          # raw, escape при отображении
        inviter_nickname_safe = html.escape(inviter_nickname)
        inviter_chat_id  = invite['inviter_chat_id']

        player = get_player(user_id)
        if not player:
            await state.clear()
            await message.answer("Сначала зарегистрируйся! /start")
            return

        # Проверяем, не занят ли организатор уже в другой паре
        if inviter_id in coop_raid_pairs:
            await state.clear()
            await message.answer(
                f"{E_CROSS} Организатор уже в другой co-op паре.",
                reply_markup=get_main_kb(),
            )
            return

        # Формируем пару
        coop_raid_pairs[inviter_id] = user_id
        coop_raid_pairs[user_id]    = inviter_id

        my_nick = html.escape(player['nickname'])

        # Переводим себя в лобби (храним уже escaped nickname партнёра для боевых сообщений)
        await state.set_state(CoopRaidState.in_lobby)
        await state.update_data(coop_partner_id=inviter_id, coop_partner_nickname=inviter_nickname_safe)

        lobby_text = (
            f"{E_SWORD} <b>CO-OP РЕЙД — ЛОББИ</b>\n\n"
            f"{E_PROFILE} {inviter_nickname_safe}\n"
            f"{E_PROFILE} {my_nick}\n\n"
            f"{E_HOURGLASS} Ожидаем, пока партнёр начнёт рейд...\n"
            f"Нажми ❌ Отменить рейд, если передумал."
        )
        await message.answer(lobby_text, reply_markup=get_coop_lobby_kb())

        # Уведомляем организатора
        notify = (
            f"{E_CHECK} {my_nick} принял приглашение!\n\n"
            f"{E_SWORD} Иди в меню {E_TICKET} <b>Рейд</b> и нажми\n"
            f"🤝 <b>Начать совместный рейд</b>"
        )
        try:
            await bot.send_message(
                chat_id=inviter_chat_id,
                text=notify,
                parse_mode="HTML",
            )
        except Exception:
            pass

    elif text == "❌ Отклонить рейд":
        invite = coop_raid_invites.pop(user_id, None)
        await state.clear()
        await message.answer(
            f"{E_CROSS} Ты отклонил приглашение.",
            reply_markup=get_main_kb(),
        )
        if invite:
            player = get_player(user_id)
            my_nick = html.escape(player['nickname']) if player else 'Игрок'
            try:
                await bot.send_message(
                    chat_id=invite['inviter_chat_id'],
                    text=f"{E_CROSS} {my_nick} отклонил приглашение на co-op рейд.",
                    parse_mode="HTML",
                )
            except Exception:
                pass
    else:
        await message.answer(
            "Прими или откажись от приглашения:",
            reply_markup=get_coop_invite_kb(),
        )


# --- Лобби: ожидание старта (принявший игрок) ---
@router.message(CoopRaidState.in_lobby)
async def handle_coop_lobby(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text    = message.text

    if text == "❌ Отменить рейд":
        data       = await state.get_data()
        partner_id = data.get('coop_partner_id')

        coop_raid_pairs.pop(user_id,    None)
        coop_raid_pairs.pop(partner_id, None)

        player = get_player(user_id)
        my_nick = html.escape(player['nickname']) if player else 'Партнёр'

        await state.clear()
        await show_main_menu(message, state)

        if partner_id:
            try:
                await bot.send_message(
                    chat_id=partner_id,
                    text=(
                        f"{E_CROSS} {my_nick} отменил совместный рейд.\n"
                        f"Ты вернулся в главное меню."
                    ),
                    reply_markup=get_main_kb(),
                    parse_mode="HTML",
                )
                partner_state = dp.fsm.resolve_context(bot, partner_id, partner_id)
                await partner_state.clear()
            except Exception:
                pass
    else:
        await message.answer(
            f"{E_HOURGLASS} Ожидаем начала рейда от партнёра...",
            reply_markup=get_coop_lobby_kb(),
        )


# --- Активный CO-OP бой ---
@router.message(CoopRaidState.in_raid)
async def coop_raid_battle_round(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    action  = message.text
    player  = get_player(user_id)
    data    = await state.get_data()

    if not player:
        await state.clear()
        await message.answer(f"{E_CROSS} Ошибка: игрок не найден.", reply_markup=get_main_kb())
        return

    # Ждём своего хода
    if not data.get('coop_is_my_turn', False):
        await message.answer(
            f"{E_HOURGLASS} Сейчас ход партнёра, подожди!",
            reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True),
        )
        return

    # Cooldown 2 сек
    if not can_battle_action(user_id):
        await message.answer("⏳ Подожди перед следующим ходом!")
        return

    floor_id         = data.get('coop_floor', 1)
    partner_id       = data.get('coop_partner_id')
    enemy_info       = RAID_FLOORS[floor_id]
    my_health        = data.get('coop_my_health', 1)
    my_damage        = data.get('coop_my_damage', 0)
    enemy_health     = data.get('coop_enemy_health', 0)
    enemy_base_dmg   = data.get('coop_enemy_base_damage', enemy_info['base_damage'])
    my_mana          = data.get('coop_my_mana', 100)
    enemy_skip_turn  = data.get('coop_enemy_skip_turn', False)
    my_blind_turns   = data.get('coop_my_blind_turns', 0)
    partner_health   = data.get('coop_partner_health', 0)
    partner_nickname = data.get('coop_partner_nickname', 'Партнёр')
    my_nick          = html.escape(player['nickname'])

    # Валидация действия
    valid_actions = {"🗡️ Атаковать", "Крит💥20%"}
    for sk_id, sk in SKILLS.items():
        if has_purchased_skill(user_id, sk_id):
            valid_actions.add(f"✨ Скилл {sk_id}: {sk['name']}")

    if action not in valid_actions:
        if action == "🏠 В главное меню":
            await _coop_raid_forfeit(user_id, partner_id, state, message)
            return
        await message.answer("Выбери действие!", reply_markup=get_battle_action_kb(user_id, my_mana))
        return

    log            = f"{E_SWORD} <b>CO-OP РЕЙД — Этаж {floor_id}/10</b>\n\n"
    new_enemy_hp   = enemy_health
    new_my_hp      = my_health
    new_mana       = my_mana
    new_enemy_skip = False
    new_my_blind   = max(0, my_blind_turns - 1)
    player_hit     = 0

    # ============ Обработка действия ============
    skill_used = None
    for sk_id, sk in SKILLS.items():
        if action == f"✨ Скилл {sk_id}: {sk['name']}":
            skill_used = (sk_id, sk)
            break

    if skill_used:
        sk_id, sk = skill_used
        if my_mana < sk['mana_cost']:
            await message.answer(
                f"{E_CROSS} Недостаточно маны! Требуется {sk['mana_cost']}{E_MANA}",
                reply_markup=get_battle_action_kb(user_id, my_mana),
            )
            return
        new_mana -= sk['mana_cost']
        log += f"✨ <b>{sk['name']}</b>!\n"

        if roll_miss():
            increment_player_dodges(user_id)
            log += f"{E_CROSS}{E_ATK} Промах! Враг уклонился\n\n"
            player_hit = 0
        elif sk_id == 1:   # Мега-молот
            player_hit = int(round(my_damage * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            log += f"{E_PROFILE} {my_nick} наносит {player_hit} урона! {E_ARROW_UP}\n"
            if random.random() < sk['stun_chance']:
                new_enemy_skip = True
                log += f"😵 Враг оглушён и пропустит следующий ход!\n"
        elif sk_id == 2:   # Кровавое неистовство
            player_hit = int(round(my_damage * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            hp_loss = max(1, int(round(calculate_player_health(player['strength']) * sk['hp_loss_pct'])))
            new_my_hp = max(1, new_my_hp - hp_loss)
            log += f"🩸 Ты теряешь {hp_loss} HP!\n"
            log += f"{E_PROFILE} {my_nick} наносит {player_hit} урона! {E_ARROW_UP}\n"
        elif sk_id == 3:   # Ослепляющая вспышка
            player_hit = 0
            new_my_blind = sk['blind_turns']
            log += f"🔦 Враг ослеплён на {sk['blind_turns']} хода! (-50% точности)\n"
        else:
            player_hit = int(round(my_damage * random.uniform(0.8, 1.2)))
        log += "\n"

    elif action == "Крит💥20%":
        is_crit = random.random() < 0.20
        if not is_crit:
            increment_player_dodges(user_id)
            log += f"{E_CROSS}{E_ATK} Ты промахиваешься!\n{E_SQ}Неудачный крит.\n\n"
            player_hit = 0
            # Враг всё равно контратакует при неудачном крите
            if enemy_skip_turn:
                log += f"😵 {enemy_info['name']} оглушён, пропускает ход!\n\n"
            else:
                b_extra = SKILLS[3]['miss_chance_add'] if new_my_blind > 0 else 0.0
                if roll_miss(b_extra):
                    increment_player_dodges(user_id)
                    log += f"{E_CROSS}{E_ATK} {enemy_info['name']} промахивается!\n\n"
                else:
                    e_hit = int(round(enemy_base_dmg * random.uniform(0.7, 1.3)))
                    new_my_hp = int(round(new_my_hp - e_hit))
                    log += (
                        f"{E_SKULL} {enemy_info['name']} контратакует! {E_ARROW_DN}\n"
                        f"{E_DMG}{E_HEART_B} Урон тебе: {e_hit}\n\n"
                    )
            if new_my_hp <= 0:
                await _coop_raid_player_died(user_id, partner_id, state, message,
                                             floor_id, player, enemy_info, log)
                return
            log += _fmt_coop_stats(
                my_nick, new_my_hp, my_damage, new_mana,
                partner_nickname, partner_health,
                enemy_info['name'], enemy_info['emoji'], new_enemy_hp, enemy_base_dmg,
            )
            await _coop_pass_turn(user_id, partner_id, state, message, log,
                                  new_my_hp, new_enemy_hp, new_mana,
                                  new_enemy_skip, new_my_blind,
                                  partner_health, partner_nickname, floor_id)
            return

        # Крит успешен
        if roll_miss():
            player_hit = 0
            increment_player_dodges(user_id)
            log += f"{E_CROSS}{E_ATK} Промах! Враг уклонился\n\n"
        else:
            base_dmg   = int(round(my_damage * random.uniform(0.8, 1.2)))
            player_hit = base_dmg * 2
            log += (
                f"{E_DMG} КРИТИЧЕСКИЙ УДАР! {E_ARROW_UP}\n"
                f"{E_PROFILE} {my_nick} атакует!\n"
                f"{E_DMG}{E_ESWORD} Урон врагу: {player_hit}\n\n"
            )
    else:
        # Обычная атака
        if roll_miss():
            player_hit = 0
            increment_player_dodges(user_id)
            log += f"{E_CROSS}{E_ATK} Промах! Враг уклонился\n\n"
        else:
            player_hit = int(round(my_damage * random.uniform(0.8, 1.2)))
            log += (
                f"{E_BELL}{E_DMG} Ты ударяешь!\n\n"
                f"{E_PROFILE} {my_nick} атакует! {E_ARROW_UP}\n"
                f"{E_DMG}{E_ESWORD} Урон врагу: {player_hit}\n\n"
            )

    new_enemy_hp = int(round(new_enemy_hp - player_hit))

    # Победа на этаже
    if new_enemy_hp <= 0:
        # Передаём актуальный HP врага (0) в state перед вызовом хелпера
        await state.update_data(coop_my_health=new_my_hp, coop_my_mana=new_mana)
        await _coop_floor_victory(user_id, partner_id, state, message, floor_id, player)
        return

    # Контратака врага на этого игрока
    if enemy_skip_turn:
        log += f"😵 {enemy_info['name']} оглушён, пропускает ход!\n\n"
    else:
        b_extra = SKILLS[3]['miss_chance_add'] if new_my_blind > 0 else 0.0
        if roll_miss(b_extra):
            increment_player_dodges(user_id)
            log += f"{E_CROSS}{E_ATK} {enemy_info['name']} промахивается!\n\n"
        else:
            e_hit = int(round(enemy_base_dmg * random.uniform(0.7, 1.3)))
            new_my_hp = int(round(new_my_hp - e_hit))
            log += (
                f"{E_SKULL} {enemy_info['name']} контратакует! {E_ARROW_DN}\n"
                f"{E_DMG}{E_HEART_B} Урон тебе: {e_hit}\n\n"
            )

    # Смерть после контратаки
    if new_my_hp <= 0:
        await _coop_raid_player_died(user_id, partner_id, state, message,
                                     floor_id, player, enemy_info, log)
        return

    # Блок статов и передача хода
    log += _fmt_coop_stats(
        my_nick, new_my_hp, my_damage, new_mana,
        partner_nickname, partner_health,
        enemy_info['name'], enemy_info['emoji'], new_enemy_hp, enemy_base_dmg,
    )
    await _coop_pass_turn(
        user_id, partner_id, state, message, log,
        new_my_hp, new_enemy_hp, new_mana,
        new_enemy_skip, new_my_blind,
        partner_health, partner_nickname, floor_id,
    )


@router.message(BattleState.in_battle, F.text == "⚔️ Начать сражение")
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
        turn_text = (
            f"{E_HASHTAG} Сейчас твой ход!\n"
            f"{E_SQ} ты ходишь первым:\n\n"
            f"{_fmt_player_stats(html.escape(player['nickname']), data['player_health'], data['player_damage'], mana)}\n\n"
            f"{_fmt_enemy_stats(enemy_info['name'], data['enemy_health'], data['enemy_damage'])}"
        )
        
        await message.answer(turn_text, reply_markup=get_battle_action_kb(user_id, mana))
        await state.update_data(player_goes_first=True)
        await state.set_state(BattleState.battle_round)
    else:
        await message.answer(f"{E_WARN} Враг ходит первым!", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await asyncio.sleep(2)
        
        enemy_damage = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
        new_player_health = int(round(data['player_health'] - enemy_damage))
        
        battle_log = (
            f"{E_SKULL} {enemy_info['name']} атакует! {E_ARROW_DN}\n"
            f"{E_DMG}{E_HEART_B} Урон тебе: {enemy_damage}\n\n"
        )
        
        if new_player_health <= 0:
            if not data.get('is_location_battle'):
                update_rating_points(user_id, -10)
            increment_player_deaths(user_id)
            battle_log += _fmt_defeat(html.escape(player['nickname']), enemy_info['name'], data.get('is_location_battle'))
            
            await message.answer(battle_log, reply_markup=get_end_battle_kb())
            await state.clear()
            return
        
        battle_log += (
            f"{_fmt_player_stats(html.escape(player['nickname']), new_player_health, data['player_damage'], mana)}\n\n"
            f"{_fmt_enemy_stats(enemy_info['name'], data['enemy_health'], data['enemy_damage'])}"
        )
        
        await message.answer(battle_log, reply_markup=get_battle_action_kb(user_id, mana))
        await state.update_data(player_goes_first=False, player_health=new_player_health)
        await state.set_state(BattleState.battle_round)

@router.message(BattleState.battle_round)
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
    battle_log = ""

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
                f"{E_CROSS} Недостаточно маны! Требуется {sk['mana_cost']}{E_MANA}",
                reply_markup=get_battle_action_kb(user_id, mana)
            )
            return
        new_mana -= sk['mana_cost']
        battle_log += f"✨ {sk['name']}!\n"

        if roll_miss():
            increment_player_dodges(user_id)
            battle_log += f"{E_CROSS}{E_ATK} Промах! Враг уклонился\n\n"
            player_hit = 0
        elif sk_id == 1:
            player_hit = int(round(data['player_damage'] * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            battle_log += f"{E_PROFILE} {html.escape(player['nickname'])} наносит {player_hit} урона! {E_ARROW_UP}\n"
            if random.random() < sk['stun_chance']:
                new_enemy_skip = True
                battle_log += "😵 Враг оглушён и пропустит следующий ход!\n"
        elif sk_id == 2:
            player_hit = int(round(data['player_damage'] * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            hp_loss = max(1, int(round(calculate_player_health(player['strength']) * sk['hp_loss_pct'])))
            new_player_health = max(1, new_player_health - hp_loss)
            battle_log += f"🩸 Вы теряете {hp_loss} HP!\n"
            battle_log += f"{E_PROFILE} {html.escape(player['nickname'])} наносит {player_hit} урона! {E_ARROW_UP}\n"
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
            increment_player_dodges(user_id)
            battle_log += (
                f"{E_CROSS}{E_ATK} Ты промахиваешься!\n"
                f"{E_SQ}Неудачный крит шанс.\n\n"
            )
            if enemy_skip_turn:
                battle_log += f"😵 {enemy_info['name']} оглушён, пропускает ход!\n\n"
                battle_log += (
                    f"{_fmt_player_stats(html.escape(player['nickname']), new_player_health, data['player_damage'], new_mana)}\n\n"
                    f"{_fmt_enemy_stats(enemy_info['name'], new_enemy_health, data['enemy_damage'])}"
                )
                await message.answer(battle_log, reply_markup=get_battle_action_kb(user_id, new_mana))
                await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health,
                                        player_mana=new_mana, enemy_skip_turn=False, player_blind_turns=new_player_blind)
                return
            enemy_damage = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
            new_player_health = int(round(new_player_health - enemy_damage))
            battle_log += (
                f"{E_SKULL} {enemy_info['name']} атакует тебя! {E_ARROW_DN}\n"
                f"{E_DMG}{E_HEART_B} Урон тебе: {enemy_damage}\n\n"
            )
            if new_player_health <= 0:
                if not data.get('is_location_battle'):
                    update_rating_points(user_id, -10)
                increment_player_deaths(user_id)
                battle_log += _fmt_defeat(html.escape(player['nickname']), enemy_info['name'], data.get('is_location_battle'))
                await message.answer(battle_log, reply_markup=get_end_battle_kb())
                await state.clear()
                return
            battle_log += (
                f"{_fmt_player_stats(html.escape(player['nickname']), new_player_health, data['player_damage'], new_mana)}\n\n"
                f"{_fmt_enemy_stats(enemy_info['name'], new_enemy_health, data['enemy_damage'])}"
            )
            await message.answer(battle_log, reply_markup=get_battle_action_kb(user_id, new_mana))
            await state.update_data(player_health=new_player_health, enemy_health=new_enemy_health,
                                    player_mana=new_mana, enemy_skip_turn=new_enemy_skip, player_blind_turns=new_player_blind)
            return
        if roll_miss():
            player_hit = 0
            increment_player_dodges(user_id)
            battle_log += f"{E_CROSS}{E_ATK} Промах! Враг уклонился\n\n"
        else:
            base_damage = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
            player_hit = base_damage * 2
            battle_log += f"{E_DMG} КРИТИЧЕСКИЙ УДАР! {E_ARROW_UP}\n{E_PROFILE} {html.escape(player['nickname'])} атакует!\n{E_DMG}{E_ESWORD} Урон врагу: {player_hit}\n\n"
    else:
        if roll_miss():
            player_hit = 0
            increment_player_dodges(user_id)
            battle_log += f"{E_CROSS}{E_ATK} Промах! Враг уклонился\n\n"
        else:
            player_hit = int(round(data['player_damage'] * random.uniform(0.8, 1.2)))
            battle_log += (
                f"{E_BELL}{E_DMG} Ты ударяешь! \n\n"
                f"{E_PROFILE} {html.escape(player['nickname'])} атакует! {E_ARROW_UP}\n"
                f"{E_DMG}{E_ESWORD} Урон врагу: {player_hit}\n\n"
            )

    new_enemy_health = int(round(new_enemy_health - player_hit))

    if new_enemy_health <= 0:
        if data.get('is_location_battle') and data.get('location_enemy_cfg'):
            increment_player_pve_wins(user_id)
            loc_cfg = data['location_enemy_cfg']
            loc_rewards = loc_cfg.get('rewards', {})
            reward_lines = []
            if 'coins' in loc_rewards:
                coin_earned = random.randint(*loc_rewards['coins'])
                add_coins_to_player(user_id, coin_earned)
                reward_lines.append(f"{E_PLUS} {coin_earned} {E_COINS} монет")
            if 'rating_points' in loc_rewards:
                rp = loc_rewards['rating_points']
                update_rating_points(user_id, rp)
                reward_lines.append(f"{E_PLUS} {rp} 💠 очков рейтинга")
            if 'food' in loc_rewards:
                food_chance = loc_rewards.get('food_chance', 1.0)
                if random.random() < food_chance:
                    food_earned = random.randint(*loc_rewards['food'])
                    add_inventory_material(user_id, 'food', food_earned)
                    reward_lines.append(f"{E_PLUS} {food_earned} {E_FOOD} еды")
            if 'wood' in loc_rewards:
                wood_earned = random.randint(*loc_rewards['wood'])
                add_inventory_material(user_id, 'wood', wood_earned)
                reward_lines.append(f"{E_PLUS} {wood_earned} {E_WOOD} древесина")
            if 'experience' in loc_rewards:
                exp_earned = random.randint(*loc_rewards['experience'])
                add_experience_to_player(user_id, exp_earned)
                reward_lines.append(f"{E_PLUS} {exp_earned} {E_EXP} опыта")
            if 'clan_exp' in loc_rewards:
                clan_exp_earned = random.randint(*loc_rewards['clan_exp'])
                player_clan = get_player_clan(user_id)
                if player_clan:
                    add_clan_exp(player_clan['clan_id'], clan_exp_earned)
                    reward_lines.append(f"{E_PLUS} {clan_exp_earned} {E_CLAN_BOTTLE} опыта клана")
            if 'crystals' in loc_rewards:
                cryst_chance = loc_rewards.get('crystals_chance', 1.0)
                if random.random() < cryst_chance:
                    cryst_earned = loc_rewards['crystals']
                    add_crystals_to_player(user_id, cryst_earned)
                    reward_lines.append(f"{E_PLUS} {cryst_earned} {E_CRYSTALS} кристалл")
            battle_log += _fmt_victory(enemy_info['name'], reward_lines)
            await message.answer(battle_log, reply_markup=get_end_battle_kb())
            await state.clear()
            return
        reward = enemy_info['reward']
        add_coins_to_player(user_id, reward)
        rating_pts = enemy_info.get('rating_points', 5)
        update_rating_points(user_id, rating_pts)
        increment_player_pve_wins(user_id)
        player_clan = get_player_clan(user_id)
        if player_clan:
            add_clan_exp(player_clan['clan_id'], 10)
        
        reward_lines = [
            f"{E_PLUS} {reward} {E_COINS} монет",
            f"{E_PLUS} {rating_pts} 💠 очков рейтинга",
        ]
        if player_clan:
            reward_lines.append(f"{E_PLUS} 10 опыта клану")
        battle_log += _fmt_victory(enemy_info['name'], reward_lines)
        
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
            increment_player_dodges(user_id)
            battle_log += f"{E_CROSS}{E_ATK} {enemy_info['name']} промахивается!\n\n"
            enemy_damage_dealt = 0
        else:
            enemy_damage_dealt = int(round(data['enemy_damage'] * random.uniform(0.7, 1.3)))
            new_player_health = int(round(new_player_health - enemy_damage_dealt))
            battle_log += (
                f"{E_SKULL} {enemy_info['name']} контратакует! {E_ARROW_DN}\n"
                f"{E_DMG}{E_HEART_B} Урон тебе: {enemy_damage_dealt}\n\n"
            )
    
    if new_player_health <= 0:
        if not data.get('is_location_battle'):
            update_rating_points(user_id, -10)
        increment_player_deaths(user_id)
        battle_log += _fmt_defeat(html.escape(player['nickname']), enemy_info['name'], data.get('is_location_battle'))
        await message.answer(battle_log, reply_markup=get_end_battle_kb())
        await state.clear()
        return
    
    battle_log += (
        f"\n{_fmt_player_stats(html.escape(player['nickname']), new_player_health, data['player_damage'], new_mana)}\n\n"
        f"{_fmt_enemy_stats(enemy_info['name'], new_enemy_health, data['enemy_damage'])}"
    )
    
    await message.answer(battle_log, reply_markup=get_battle_action_kb(user_id, new_mana))
    await state.update_data(
        player_health=new_player_health,
        enemy_health=new_enemy_health,
        player_mana=new_mana,
        enemy_skip_turn=new_enemy_skip,
        player_blind_turns=new_player_blind,
    )

@router.message(BattleState.in_battle, F.text == "❌ Назад")
async def back_to_enemies(message: types.Message, state: FSMContext):
    await show_main_menu(message, state)

@router.message(F.text == "🏠 В главное меню")
async def back_to_main(message: types.Message, state: FSMContext):
    await show_main_menu(message, state)

# ============== ONLINE (PvP) ==============
@router.message(F.text == "🌐 Онлайн")
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

    mana = 100

    online_text = (
        f'{E_ONLINE2}{E_SWORD} ОНЛАЙН РЕЖИМ:\n'
        f'{E_SQ}Начните подбор игрока, нажав на кнопку.\n\n'
        f'{E_PROFILE} Характеристики {html.escape(player["nickname"])}:\n\n'
        f'{E_SQ}{player.get("rating_points", 0)} {E_STAR} Points\n'
        f'{E_SQ}{get_league_label(player.get("rating_points", 0))}\n\n'
        f'{E_SQ}{E_ATK} {int(buffed_strength)} Сила {E_YELLOW}\n'
        f'{E_SQ}{E_HP} {health} Здоровье {E_YELLOW}\n'
        f'{E_SQ}{E_DMG} {damage} Урон {E_YELLOW}\n'
        f'{E_SQ}{E_MANA} {mana} / 100 {E_BOOK_MANA}{E_YELLOW}\n\n'
        f'{E_WARN} внимание! любой абуз рейтинга с помощью твинков и тд, карается баном навсегда по айди профиля!\n'
    )
    await send_image_with_text(message, "images/online.png", online_text, reply_markup=get_online_menu_kb())
    await state.set_state(OnlineState.viewing_menu)


@router.message(OnlineState.viewing_menu, F.text == "❌ Выйти из онлайна")
async def leave_online_menu(message: types.Message, state: FSMContext):
    await show_main_menu(message, state)


@router.message(OnlineState.viewing_menu, F.text == "🔍 Поиск игрока")
async def start_online_search(message: types.Message, state: FSMContext):
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
        f'{E_SQ}{E_SEARCH} ищем соперника... {E_GREEN}'
    )

    pvp_queue[user_id] = {
        "nickname": html.escape(player['nickname']),
        "strength": buffed_strength,
        "wins": player['wins'],
        "health": health,
        "damage": damage,
        "chat_id": message.chat.id
    }

    await send_image_with_text(message, "images/search.png", search_text, reply_markup=get_searching_kb())
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
            f'{E_SWORD} <b>СОПЕРНИК НАЙДЕН!</b>\n\n'
            f'{E_PROFILE} Характеристики {html.escape(opponent_data["nickname"])}:\n\n'
            f'{E_SQ}{E_ATK} {int(opponent_data["strength"])} Сила {E_YELLOW}\n'
            f'{E_SQ}{E_HP} {opponent_data["health"]} Здоровье {E_YELLOW}\n'
            f'{E_SQ}{E_DMG} {opponent_data["damage"]} Урон {E_YELLOW}\n\n'
            f'{E_LOCK} примите игру, чтобы начать битву'
        )
        match_text_opp = (
            f'{E_SWORD} <b>СОПЕРНИК НАЙДЕН!</b>\n\n'
            f'{E_PROFILE} Характеристики {html.escape(my_data["nickname"])}:\n\n'
            f'{E_SQ}{E_ATK} {int(my_data["strength"])} Сила {E_YELLOW}\n'
            f'{E_SQ}{E_HP} {my_data["health"]} Здоровье {E_YELLOW}\n'
            f'{E_SQ}{E_DMG} {my_data["damage"]} Урон {E_YELLOW}\n\n'
            f'{E_LOCK} примите игру, чтобы начать битву'
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


@router.message(OnlineState.searching, F.text == "🚫 Прекратить поиск")
async def stop_searching(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    pvp_queue.pop(user_id, None)
    await state.clear()
    await message.answer("Поиск отменён.", reply_markup=get_main_kb())


@router.message(OnlineState.waiting_accept)
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
                        text=f"{E_CROSS} Соперник отклонил игру.",
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

            first_name = html.escape(my_player['nickname']) if player_goes_first else html.escape(opp_player['nickname'])
            start_text = f'{E_HASHTAG} <b>PvP БОЙ НАЧАЛСЯ!</b>\n\nПервым ходит: {first_name}\n'

            if player_goes_first:
                await message.answer(
                    start_text + f'\n{E_SQ} Твой ход!\n{E_SQ}{E_MANA} Мана: 100/100 {E_BOOK_MANA}',
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
                    text=start_text + f'\n{E_SQ} Твой ход!\n{E_SQ}{E_MANA} Мана: 100/100 {E_BOOK_MANA}',
                    reply_markup=get_battle_action_kb(opponent_id, 100),
                    parse_mode="HTML"
                )
        else:
            await message.answer("✅ Вы приняли. Ожидаем соперника...", reply_markup=get_pvp_accept_kb())


@router.message(OnlineState.in_pvp_battle)
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

    my_player = get_player(user_id)
    my_nick = html.escape(my_player['nickname']) if my_player else 'Игрок'

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
                f"{E_CROSS} Недостаточно маны! Требуется {sk['mana_cost']}{E_MANA}",
                reply_markup=get_battle_action_kb(user_id, my_mana)
            )
            return
        new_my_mana -= sk['mana_cost']
        battle_log += f"✨ {sk['name']}!\n"

        if roll_miss():
            dealt = 0
            increment_player_dodges(user_id)
            battle_log += f"{E_CROSS}{E_ATK} Промах! Соперник уклонился\n\n"
        elif sk_id == 1:
            dealt = int(round(my_damage * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            battle_log += f'Ты наносишь {dealt} урона! {E_ARROW_UP}\n'
            if random.random() < sk['stun_chance']:
                opp_should_skip = True
                battle_log += "😵 Соперник оглушён и пропустит следующий ход!\n"
        elif sk_id == 2:
            dealt = int(round(my_damage * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            hp_loss = max(1, int(round(my_health * sk['hp_loss_pct'])))
            my_health = max(1, my_health - hp_loss)
            battle_log += f'🩸 Ты теряешь {hp_loss} HP!\n'
            battle_log += f'Ты наносишь {dealt} урона! {E_ARROW_UP}\n'
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
            increment_player_dodges(user_id)
            battle_log += (
                f"{E_CROSS}{E_ATK} Ты промахиваешься!\n"
                f"{E_SQ}Неудачный крит шанс.\n\n"
            )
        elif roll_miss():
            dealt = 0
            increment_player_dodges(user_id)
            battle_log += f"{E_CROSS}{E_ATK} Промах! Соперник уклонился\n\n"
        else:
            base = int(round(my_damage * random.uniform(0.8, 1.2)))
            dealt = base * 2
            battle_log += f'{E_DMG} КРИТИЧЕСКИЙ УДАР! {E_ARROW_UP}\n{E_DMG}{E_ESWORD} Урон сопернику: {dealt}\n\n'
    else:
        if roll_miss():
            dealt = 0
            increment_player_dodges(user_id)
            battle_log += f"{E_CROSS}{E_ATK} Промах! Соперник уклонился\n\n"
        else:
            dealt = int(round(my_damage * random.uniform(0.8, 1.2)))
            battle_log += (
                f'{E_BELL}{E_DMG} Ты ударяешь!\n\n'
                f'{E_DMG}{E_ESWORD} Урон сопернику: {dealt}\n\n'
            )

    new_enemy_health = int(round(enemy_health - dealt))

    if new_enemy_health <= 0:
        update_player_wins(user_id)
        my_rating = my_player.get('rating_points', 0) if my_player else 0
        win_pts, _ = get_pvp_league_points(my_rating)
        update_rating_points(user_id, win_pts)
        add_online_match(user_id)
        if opponent_id:
            add_online_match(opponent_id)
            increment_player_deaths(opponent_id)
            opp_p = get_player(opponent_id)
            if opp_p:
                _, loss_pts = get_pvp_league_points(opp_p['rating_points'])
                update_rating_points(opponent_id, -loss_pts)
        winner_clan = get_player_clan(user_id)
        if winner_clan:
            add_clan_exp(winner_clan['clan_id'], 2)
        battle_log += (
            f"{E_CHART} Результаты боя:\n\n"
            f"{E_TROPHY}{E_GREEN} ВЫ ПОБЕДИЛИ!\n\n"
            f"{E_GIFT} Получено:\n"
            f"{E_PLUS} +1 победа\n"
            f"{E_PLUS} +{win_pts} 💠 рейтинга\n"
        )
        await message.answer(battle_log, reply_markup=get_end_battle_kb())
        pvp_pairs.pop(user_id, None)
        pvp_pairs.pop(opponent_id, None)
        await state.clear()

        if opponent_id:
            opp_state = dp.fsm.resolve_context(bot, opponent_id, opponent_id)
            await opp_state.clear()
            try:
                if dealt > 0:
                    dmg_line = f'{E_DMG}{E_HEART_B} Урон тебе: {dealt}\n\n'
                else:
                    dmg_line = f'{E_CROSS}{E_ATK} {my_nick} промахнулся!\n\n'
                opp_loss_text = (
                    f'⚔️ <b>PvP БОЙ</b> ⚔️\n\n'
                    f'{E_SKULL} {my_nick} атакует! {E_ARROW_DN}\n'
                    + dmg_line
                    + f'{E_BOOK_LOSS}{E_RED_C} ВЫ ПРОИГРАЛИ!'
                )
                await bot.send_message(
                    chat_id=opponent_id,
                    text=opp_loss_text,
                    reply_markup=get_end_battle_kb(),
                    parse_mode="HTML"
                )
            except Exception:
                pass
        return

    # Передаём ход сопернику
    opp_player = get_player(opponent_id) if opponent_id else None
    opp_nick = html.escape(opp_player['nickname']) if opp_player else 'Соперник'
    battle_log += (
        f'{E_CROWN} Ты: {E_HP} {my_health} | {E_MANA} {new_my_mana}/100\n'
        f'{E_SKULL} {opp_nick}: {E_ESWORD} {new_enemy_health}\n\n'
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
            if dealt > 0:
                opp_dmg_line = f'{E_DMG}{E_HEART_B} Урон тебе: {dealt}\n\n'
            else:
                opp_dmg_line = f'{E_CROSS}{E_ATK} {my_nick} промахнулся!\n\n'
            opp_msg = (
                f'⚔️ <b>PvP БОЙ</b> ⚔️\n\n'
                f'{E_SKULL} {my_nick} атакует! {E_ARROW_DN}\n'
                + opp_dmg_line
            )
            if opp_should_skip:
                opp_msg += "😵 Ты оглушён и пропустишь следующий ход!\n"
            if opp_blind_add > 0:
                opp_msg += f"🔦 Ты ослеплён на {opp_blind_add} хода!\n"
            opp_msg += (
                f'\n{E_CROWN} Ты: {E_HP} {new_opp_player_health} | {E_MANA} {opp_mana}/100\n'
                f'{E_SKULL} {my_nick}: {E_ESWORD} {my_health}\n\n'
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
                    f'{E_SKULL} {opp_nick}: {E_ESWORD} {new_enemy_health}\n\n'
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
        exp_display = f'<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji> {clan["clan_exp"]} / {max_exp} <tg-emoji emoji-id="6284926868026037181">🍾</tg-emoji>'
    co_leaders = get_clan_co_leaders(clan['clan_id'])
    co_str = ", ".join(nick for _, nick in co_leaders) if co_leaders else "—"
    return (
        f"| {E_CLAN} | Клан: {html.escape(clan['clan_name'])}\n"
        f"| {E_CROWN} | Глава: {html.escape(leader_nickname)}\n"
        f"| {E_CLAN_STAR} | Соруководители: {html.escape(co_str)}\n"
        f"{E_CLAN_EXP} - {clan['members_count']} соклановцев\n"
        f"(Минимальный порог входа) - {clan['min_power']} {E_ATK}\n"
        f"Уровень клана - {clan['clan_level']} {E_CLAN_LVL}\n"
        f"{exp_display}\n\n"
        f"| {E_BOOK} | Описание клана:\n{html.escape(clan['description'] or '—')}"
    )

@router.message(F.text == "🛡️ Кланы")
async def open_clans(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    my_clan = get_player_clan(user_id)
    if my_clan:
        is_leader = (my_clan['leader_id'] == user_id)
        is_co_leader = not is_leader and get_clan_member_role(user_id, my_clan['clan_id']) == 'co_leader'
        await _show_clan_info(message, my_clan, is_leader, is_co_leader)
        await state.set_state(ClanMenu.viewing_my_clan)
        await state.update_data(clan_id=my_clan['clan_id'])
    else:
        clans = get_all_clans()
        if clans:
            clans_text = "🛡️ <b>СПИСОК КЛАНОВ</b>\n\n"
            for clan in clans:
                _, name, lvl, members, min_power, ldr = clan
                clans_text += f"🛡️ {html.escape(name)} — ур.{lvl} | {members}👥 | порог: {min_power}⚔️\n"
        else:
            clans_text = "🛡️ <b>КЛАНОВ ЕЩЁ НЕТ</b>\n\nСтань первым!"
        await message.answer(clans_text, reply_markup=get_clans_list_kb(clans))
        await state.set_state(ClanMenu.viewing_clans)

@router.message(ClanMenu.viewing_clans)
async def handle_clans_list(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    text = message.text

    if text == "❌ Вернуться":
        await show_main_menu(message, state)
        return

    if text == "➕ Создать клан":
        if get_player_clan(user_id):
            await message.answer(f"{E_CROSS} Вы уже состоите в клане!", reply_markup=get_clans_list_kb(get_all_clans()))
            return
        if player['coins'] < 2000:
            await message.answer(
                f"{E_CROSS} Недостаточно монет!\nТребуется: 2000💰\nУ вас: {player['coins']}💰",
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
                await message.answer(f"{E_CROSS} Вы уже состоите в клане!")
                return
            if player['strength'] < min_power:
                await message.answer(
                    f"{E_CROSS} Ваша мощь недостаточна. Требуется {min_power}⚔️\nВаша мощь: {int(player['strength'])}⚔️",
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
            # Уведомить всех членов клана о новом участнике
            joiner = get_player(user_id)
            joiner_name = joiner['nickname'] if joiner else "Игрок"
            join_notify_text = (
                f"<tg-emoji emoji-id=\"5397916757333654639\">➕</tg-emoji> "
                f"<tg-emoji emoji-id=\"5275979556308674886\">👤</tg-emoji> в клан {clan_name}, зашёл {joiner_name}\n"
                f"<tg-emoji emoji-id=\"5267324424113124134\">▫️</tg-emoji>"
                f"<tg-emoji emoji-id=\"5906800644525660990\">🟡</tg-emoji> Приветствуем в клане! "
                f"<tg-emoji emoji-id=\"5233638274056083197\">🤩</tg-emoji>"
            )
            clan_members_list = get_clan_members(clan_id)
            for member_uid, _, _, _ in clan_members_list:
                try:
                    await bot.send_message(chat_id=member_uid, text=join_notify_text)
                except Exception:
                    pass
            return

    await message.answer("Выбери клан из списка или создай новый!", reply_markup=get_clans_list_kb(clans))

@router.message(ClanMenu.creating_clan_confirm)
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
            await message.answer(f"{E_CROSS} Недостаточно монет для создания клана!", reply_markup=get_main_kb())
            await state.clear()
            return
        remove_coins_from_player(user_id, 2000)
        await message.answer("Введите название клана:", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(ClanMenu.creating_clan_name)
        return

    await message.answer("Нажмите ✅ Да, создать или ❌ Нет", reply_markup=get_create_clan_confirm_kb())

@router.message(ClanMenu.creating_clan_name)
async def handle_create_clan_name(message: types.Message, state: FSMContext):
    clan_name = message.text.strip()
    if not clan_name or len(clan_name) > 32:
        await message.answer(f"{E_CROSS} Название должно быть от 1 до 32 символов. Введите ещё раз:")
        return
    await state.update_data(new_clan_name=clan_name)
    await message.answer("Введите описание клана:")
    await state.set_state(ClanMenu.creating_clan_description)

@router.message(ClanMenu.creating_clan_description)
async def handle_create_clan_description(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    description = message.text.strip()
    data = await state.get_data()
    clan_name = data.get('new_clan_name', '')

    clan_id = create_clan(clan_name, user_id, description)
    if clan_id == -1:
        await message.answer(f"{E_CROSS} Клан с таким названием уже существует! Попробуйте другое.")
        await state.set_state(ClanMenu.creating_clan_name)
        await message.answer("Введите название клана:")
        return

    clan = get_player_clan(user_id)
    leader = get_player(user_id)
    clan_text = _format_clan_menu(clan, leader['nickname'])
    await message.answer(f"✅ Клан создан!\n\n" + clan_text, reply_markup=get_my_clan_kb(True))
    await state.set_state(ClanMenu.viewing_my_clan)
    await state.update_data(clan_id=clan_id)

@router.message(ClanMenu.viewing_my_clan)
async def handle_my_clan(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')

    if text == "🔙 Вернуться":
        await show_main_menu(message, state)
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
        leaver = get_player(user_id)
        leaver_name = leaver['nickname'] if leaver else "Игрок"
        clan_name = clan['clan_name']
        # Получить список членов ДО выхода
        members_before = get_clan_members(clan_id)
        leave_clan(user_id, clan_id)
        await state.clear()
        clans = get_all_clans()
        await message.answer("Вы вышли из клана.", reply_markup=get_clans_list_kb(clans))
        await state.set_state(ClanMenu.viewing_clans)
        # Уведомить оставшихся членов клана
        leave_notify_text = (
            f"❌👤 из клана {clan_name}, вышел {leaver_name}\n"
            f"▫️🔴 Прощаемся с тобой. ☹️"
        )
        for member_uid, _, _, _ in members_before:
            if member_uid == user_id:
                continue
            try:
                await bot.send_message(chat_id=member_uid, text=leave_notify_text)
            except Exception:
                pass
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
        # html is imported at the top of the file
        messages = get_clan_messages(clan_id, 30)
        if messages:
            chat_text = "💬 <b>ЧАТ КЛАНА</b> (последние 30 сообщений)\n\n"
            for nick, msg, sent_at in messages:
                time_str = sent_at[:16] if sent_at else ""
                chat_text += f"[{time_str}] <b>{html.escape(nick)}</b>: {html.escape(msg)}\n"
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

    if text == "🏰 Клановый босс":
        await _open_clan_boss_menu(message, state, clan, user_id)
        return

    # Обновить и показать информацию о клане
    await _show_clan_info(message, clan, is_leader, is_co_leader)

@router.message(ClanMenu.kicking_member)
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
            await show_main_menu(message, state)
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

            # Уведомить оставшихся членов клана о выходе
            leave_notify_text = (
                f"❌👤 из клана {clan_name}, вышел {nickname}\n"
                f"▫️🔴 Прощаемся с тобой. ☹️"
            )
            for m_uid, _, _, _ in members:
                if m_uid == member_id:
                    continue
                try:
                    await bot.send_message(chat_id=m_uid, text=leave_notify_text)
                except Exception:
                    pass

            break

    if not kicked:
        await message.answer(f"{E_CROSS} Игрок не найден!",
                             reply_markup=get_kick_members_kb(members, clan['leader_id'],
                                                              co_leader_ids if is_co_leader else []))
        return

    updated_clan = get_clan(clan_id)
    leader = get_player(updated_clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(updated_clan, leader_name)
    await message.answer(clan_text, reply_markup=get_my_clan_kb(is_leader, is_co_leader))
    await state.set_state(ClanMenu.viewing_my_clan)

@router.message(ClanMenu.promoting_member)
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
            await show_main_menu(message, state)
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    if clan['leader_id'] != user_id:
        await message.answer(f"{E_CROSS} Только глава может назначать соруководителей.",
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
        await message.answer(f"{E_CROSS} Игрок не найден!",
                             reply_markup=get_promote_members_kb(members, clan['leader_id']))
        return

    updated_clan = get_clan(clan_id)
    leader = get_player(updated_clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(updated_clan, leader_name)
    await message.answer(clan_text, reply_markup=get_my_clan_kb(True))
    await state.set_state(ClanMenu.viewing_my_clan)

@router.message(ClanMenu.demoting_member)
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
            await show_main_menu(message, state)
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    if clan['leader_id'] != user_id:
        await message.answer(f"{E_CROSS} Только глава может снимать соруководителей.",
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
        await message.answer(f"{E_CROSS} Игрок не найден!",
                             reply_markup=get_demote_members_kb(co_leaders))
        return

    updated_clan = get_clan(clan_id)
    leader = get_player(updated_clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(updated_clan, leader_name)
    await message.answer(clan_text, reply_markup=get_my_clan_kb(True))
    await state.set_state(ClanMenu.viewing_my_clan)

@router.message(ClanMenu.in_clan_chat)
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
            await _show_clan_info(message, clan, is_leader, is_co_leader)
        else:
            await show_main_menu(message, state)
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    if not text:
        return

    # Validate message length
    if len(text) > CLAN_CHAT_MAX_MSG_LEN:
        await message.answer(f"{E_CROSS} Сообщение слишком длинное (максимум {CLAN_CHAT_MAX_MSG_LEN} символов).",
                             reply_markup=get_clan_chat_kb())
        return

    # Get sender nickname
    player = get_player(user_id)
    if not player:
        return
    nickname = html.escape(player['nickname'])

    # Save to DB
    save_clan_message(clan_id, user_id, nickname, text)

    # Track spam for "Какашка" status (20-30 messages in 6 seconds)
    now = datetime.now()
    if user_id not in clan_chat_spam_tracker:
        clan_chat_spam_tracker[user_id] = []
    clan_chat_spam_tracker[user_id].append(now)
    # Keep only messages from last 6 seconds
    clan_chat_spam_tracker[user_id] = [t for t in clan_chat_spam_tracker[user_id] if (now - t).total_seconds() <= 6]
    if len(clan_chat_spam_tracker[user_id]) >= 20:
        set_player_spammer_flag(user_id)

    # Broadcast to all members currently in chat session
    active_members = clan_chat_sessions.get(clan_id, set()).copy()
    from datetime import datetime
    # html is imported at the top of the file
    time_str = datetime.now().strftime("%H:%M")
    safe_nick = html.escape(nickname)
    safe_text = html.escape(text)
    broadcast_text = f"[{time_str}] <b>{safe_nick}</b>: {safe_text}"
    for member_id in active_members:
        if member_id == user_id:
            continue
        try:
            await bot.send_message(chat_id=member_id, text=broadcast_text, parse_mode="HTML")
        except Exception:
            # If sending fails, remove from active sessions
            clan_chat_sessions[clan_id].discard(member_id)

@router.message(ClanMenu.changing_min_power)
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
        await message.answer(f"{E_CROSS} Введите корректное число (≥ 0):")
        return

    set_clan_min_power(clan_id, new_power)
    updated_clan = get_clan(clan_id)
    leader = get_player(updated_clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(updated_clan, leader_name)
    await message.answer(f"✅ Порог входа обновлён: {new_power}⚔️\n\n" + clan_text,
                         reply_markup=get_my_clan_kb(True))
    await state.set_state(ClanMenu.viewing_my_clan)

@router.message(ClanMenu.deleting_clan_confirm)
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
            await message.answer(f"{E_CROSS} Ошибка при удалении клана.", reply_markup=get_main_kb())
        return

    await message.answer("Нажмите ✅ Да, удалить или ❌ Нет", reply_markup=get_delete_clan_confirm_kb())

# ============== CLAN CUSTOMIZATION ==============
async def _show_clan_info(message, clan: dict, is_leader: bool, is_co_leader: bool = False):
    """Отправить информацию о клане с картиной"""
    leader = get_player(clan['leader_id'])
    leader_name = leader['nickname'] if leader else "—"
    clan_text = _format_clan_menu(clan, leader_name)
    kb = get_my_clan_kb(is_leader, is_co_leader)

    # Сначала проверяем загруженную картинку
    if clan.get('clan_image'):
        try:
            await message.answer_photo(clan['clan_image'], caption=clan_text, reply_markup=kb)
            return
        except Exception:
            pass

    # Если нет - показываем дефолтную myclan.png
    try:
        photo = FSInputFile("images/myclan.png")
        await message.answer_photo(photo, caption=clan_text, reply_markup=kb)
        return
    except Exception:
        pass

    # Если ничего - просто текст
    await message.answer(clan_text, reply_markup=kb)

@router.message(ClanMenu.selecting_clan_customization)
async def handle_select_clan_customization(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_id')
    clan = get_clan(clan_id) if clan_id else None

    if not clan or clan['leader_id'] != user_id:
        await state.set_state(ClanMenu.viewing_my_clan)
        await message.answer(f"{E_CROSS} Ошибка доступа.", reply_markup=get_my_clan_kb(False))
        return

    if text == "❌ Отмена":
        await _show_clan_info(message, clan, True)
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    player = get_player(user_id)

    if text == "📝 Изменить название (500 монет)":
        if player['coins'] < 500:
            await message.answer(f"{E_CROSS} Недостаточно монет! Нужно 500, у вас {player['coins']}.")
            return
        await message.answer(
            "Введите новое название клана (1-32 символа):",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)
        )
        await state.set_state(ClanMenu.changing_clan_name)
        return

    if text == "📄 Изменить описание (500 монет)":
        if player['coins'] < 500:
            await message.answer(f"{E_CROSS} Недостаточно монет! Нужно 500, у вас {player['coins']}.")
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

@router.message(ClanMenu.changing_clan_name)
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
        await message.answer(f"{E_CROSS} Название должно быть от 1 до 32 символов. Введите ещё раз:")
        return

    player = get_player(user_id)
    if player['coins'] < 500:
        clan = get_clan(clan_id)
        await message.answer(f"{E_CROSS} Недостаточно монет!")
        if clan:
            await _show_clan_info(message, clan, True)
        await state.set_state(ClanMenu.viewing_my_clan)
        return

    success = update_clan_name(clan_id, new_name)
    if not success:
        await message.answer(f"{E_CROSS} Клан с таким названием уже существует! Введите другое:")
        return

    remove_coins_from_player(user_id, 500)
    updated_clan = get_clan(clan_id)
    await message.answer(f"✅ Название клана изменено на «{new_name}»!\n- 500 монет")
    await _show_clan_info(message, updated_clan, True)
    await state.set_state(ClanMenu.viewing_my_clan)

@router.message(ClanMenu.changing_clan_description)
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
        await message.answer(f"{E_CROSS} Недостаточно монет!")
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

@router.message(ClanMenu.changing_clan_image)
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
        await message.answer(f"{E_CROSS} Отправьте фото! Или нажмите ❌ Отмена.")
        return

    photo_file_id = message.photo[-1].file_id
    update_clan_image(clan_id, photo_file_id)
    set_player_clan_image_flag(message.from_user.id)
    updated_clan = get_clan(clan_id)
    await message.answer("✅ Картина клана обновлена!")
    await _show_clan_info(message, updated_clan, True)
    await state.set_state(ClanMenu.viewing_my_clan)

# ============== ADMIN PANEL ==============
@router.message(Command("67"))
async def open_admin_panel(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())
    await state.set_state(AdminPanel.main_menu)

@router.message(AdminPanel.main_menu)
async def admin_menu_handler(message: types.Message, state: FSMContext):
    text = message.text
    if text == "❌ Выход":
        await show_main_menu(message, state)
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
    if text == "🎟️ Накрутить билеты босса":
        await message.answer("Введите никнейм игрока:",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(AdminPanel.adding_boss_tickets_nickname)
        return
    if text == "🥕 Накрутить материалы":
        await message.answer("Введите никнейм игрока:",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(AdminPanel.adding_materials_nickname)
        return
    if text == "📦 Накрутить сундуки":
        await message.answer("Введите никнейм игрока:",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
        await state.set_state(AdminPanel.adding_chests_nickname)
        return
    if text == "⏩ Пропустить кд босса":
        admin_clan = get_player_clan(message.from_user.id)
        if not admin_clan:
            await message.answer(f"{E_CROSS} Вы не состоите ни в одном клане!", reply_markup=get_admin_kb())
            return
        skipped = skip_clan_boss_cooldown(admin_clan['clan_id'])
        if skipped:
            await message.answer(
                f"✅ Cooldown кланового босса в клане «{admin_clan['clan_name']}» сброшен!\n"
                f"Новый босс активен прямо сейчас.",
                reply_markup=get_admin_kb()
            )
        else:
            await message.answer(
                f"{E_CROSS} Босс в клане «{admin_clan['clan_name']}» уже активен, cooldown не требуется.",
                reply_markup=get_admin_kb()
            )
        return
    await message.answer("Выберите действие!", reply_markup=get_admin_kb())

@router.message(AdminPanel.adding_coins_nickname)
async def admin_coins_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"{E_CROSS} Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите сумму монет для добавления:")
    await state.set_state(AdminPanel.adding_coins_amount)

@router.message(AdminPanel.adding_coins_amount)
async def admin_coins_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E_CROSS} Введите корректное число:")
        return
    data = await state.get_data()
    add_coins_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount} монет добавлено игроку {html.escape(data['target_nickname'])}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

@router.message(AdminPanel.adding_strength_nickname)
async def admin_strength_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"{E_CROSS} Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите сумму силы для добавления:")
    await state.set_state(AdminPanel.adding_strength_amount)

@router.message(AdminPanel.adding_strength_amount)
async def admin_strength_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer(f"{E_CROSS} Введите корректное число:")
        return
    data = await state.get_data()
    add_strength_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount}⚔️ силы добавлено игроку {html.escape(data['target_nickname'])}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

@router.message(AdminPanel.adding_experience_nickname)
async def admin_experience_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"{E_CROSS} Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите количество опыта для добавления:")
    await state.set_state(AdminPanel.adding_experience_amount)

@router.message(AdminPanel.adding_experience_amount)
async def admin_experience_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E_CROSS} Введите корректное число:")
        return
    data = await state.get_data()
    result = add_experience_to_player(data['target_user_id'], amount)
    lvl_msg = f" (уровень повышен до {result['new_level']}!)" if result.get('leveled_up') else ""
    await message.answer(f"✅ {amount} опыта добавлено игроку {html.escape(data['target_nickname'])}{lvl_msg}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

@router.message(AdminPanel.adding_crystals_nickname)
async def admin_crystals_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"{E_CROSS} Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите количество кристаллов для добавления:")
    await state.set_state(AdminPanel.adding_crystals_amount)

@router.message(AdminPanel.adding_crystals_amount)
async def admin_crystals_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E_CROSS} Введите корректное число:")
        return
    data = await state.get_data()
    add_crystals_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount} кристаллов добавлено игроку {html.escape(data['target_nickname'])}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

@router.message(AdminPanel.adding_raid_tickets_nickname)
async def admin_raid_tickets_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"{E_CROSS} Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите количество билетов рейда для добавления:")
    await state.set_state(AdminPanel.adding_raid_tickets_amount)

@router.message(AdminPanel.adding_raid_tickets_amount)
async def admin_raid_tickets_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E_CROSS} Введите корректное число:")
        return
    data = await state.get_data()
    add_raid_tickets_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount} билетов рейда добавлено игроку {html.escape(data['target_nickname'])}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

@router.message(AdminPanel.adding_materials_nickname)
async def admin_materials_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"{E_CROSS} Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    await message.answer("Введите количество материалов для добавления (каждого вида):")
    await state.set_state(AdminPanel.adding_materials_amount)

@router.message(AdminPanel.adding_materials_amount)
async def admin_materials_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer(f"{E_CROSS} Введите корректное число:")
        return
    data = await state.get_data()
    add_admin_materials_to_player(data['target_user_id'], amount)
    await message.answer(f"✅ {amount} каждого материала добавлено игроку {html.escape(data['target_nickname'])}")
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

@router.message(AdminPanel.adding_boss_tickets_nickname)
async def admin_boss_tickets_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"{E_CROSS} Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    clan_info = get_player_clan(target['user_id'])
    if not clan_info:
        await message.answer(f"{E_CROSS} Игрок «{nickname}» не состоит в клане. Билеты босса привязаны к клану.")
        await state.set_state(AdminPanel.main_menu)
        await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'],
                            target_clan_id=clan_info['clan_id'])
    current = get_clan_boss_tickets(target['user_id'], clan_info['clan_id'])
    await message.answer(
        f"Игрок: {html.escape(target['nickname'])}\n"
        f"Текущие билеты босса: {current}/{MAX_CLAN_BOSS_TICKETS}\n\n"
        f"Введите количество билетов для добавления (макс. {MAX_CLAN_BOSS_TICKETS}):"
    )
    await state.set_state(AdminPanel.adding_boss_tickets_amount)

@router.message(AdminPanel.adding_boss_tickets_amount)
async def admin_boss_tickets_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(f"{E_CROSS} Введите корректное положительное число:")
        return
    data = await state.get_data()
    target_uid = data['target_user_id']
    target_nick = data['target_nickname']
    clan_id = data['target_clan_id']
    current = get_clan_boss_tickets(target_uid, clan_id)
    if current >= MAX_CLAN_BOSS_TICKETS:
        await message.answer(
            f"{E_CROSS} У игрока {html.escape(target_nick)} уже максимум билетов ({MAX_CLAN_BOSS_TICKETS}/{MAX_CLAN_BOSS_TICKETS})!"
        )
    else:
        new_count = add_clan_boss_tickets(target_uid, clan_id, amount)
        added = new_count - current
        await message.answer(
            f"✅ Добавлено {added} {E_CB_TICKET} билетов боссу игроку {html.escape(target_nick)}\n"
            f"Теперь у него: {new_count}/{MAX_CLAN_BOSS_TICKETS}"
        )
    await state.set_state(AdminPanel.main_menu)
    await message.answer("🔐 Админ панель", reply_markup=get_admin_kb())

_ADMIN_CHEST_KEYS = {
    "chest_wood":   "Деревянный сундук",
    "chest_steel":  "Стальной сундук",
    "chest_gold":   "Золотой сундук",
    "chest_divine": "Всевышний сундук",
}

@router.message(AdminPanel.adding_chests_nickname)
async def admin_chests_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"{E_CROSS} Игрок «{nickname}» не найден. Введите никнейм ещё раз:")
        return
    await state.update_data(target_user_id=target['user_id'], target_nickname=target['nickname'])
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Деревянный сундук")],
        [KeyboardButton(text="Стальной сундук")],
        [KeyboardButton(text="Золотой сундук")],
        [KeyboardButton(text="Всевышний сундук")],
    ], resize_keyboard=True)
    await message.answer("Выберите тип сундука:", reply_markup=kb)
    await state.set_state(AdminPanel.adding_chests_type)

@router.message(AdminPanel.adding_chests_type)
async def admin_chests_type(message: types.Message, state: FSMContext):
    name_to_key = {v: k for k, v in _ADMIN_CHEST_KEYS.items()}
    chest_key = name_to_key.get(message.text.strip())
    if not chest_key:
        await message.answer(f"{E_CROSS} Неверный тип сундука. Выберите из списка:")
        return
    await state.update_data(chest_key=chest_key)
    await message.answer(
        f"Введите количество сундуков «{_ADMIN_CHEST_KEYS[chest_key]}» для добавления:",
        reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True),
    )
    await state.set_state(AdminPanel.adding_chests_amount)

@router.message(AdminPanel.adding_chests_amount)
async def admin_chests_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(f"{E_CROSS} Введите корректное положительное число:")
        return
    data = await state.get_data()
    chest_key = data['chest_key']
    add_inventory_material(data['target_user_id'], chest_key, amount)
    chest_name = _ADMIN_CHEST_KEYS[chest_key]
    await message.answer(
        f"✅ {amount} × «{chest_name}» добавлено игроку {html.escape(data['target_nickname'])}",
        parse_mode="HTML",
    )
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

            now = datetime.now(timezone.utc)
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

# ============== MARKET ==============
# Material key -> display emoji and name (for message text display)
_MARKET_MAT_INFO = {
    'food':  (E_FOOD,   'Еду',       "Продать"),
    'wood':  (E_WOOD,   'Древесину',  "Продать"),
    'stone': (E_STONE,  'Камень',    "Продать"),
    'iron':  (E_IRON,   'Железо',    "Продать"),
    'gold':  (E_GOLD_M, 'Золото',    "Продать"),
}

# Button text -> material key (plain emoji for keyboard buttons)
_MARKET_SELL_BUTTONS = {
    "Продать еду🥕": 'food',
    "Продать древесину🌳": 'wood',
    "Продать камень🪨": 'stone',
    "Продать железо⛰": 'iron',
    "Продать золото🥇": 'gold',
}

def _get_market_category_text() -> str:
    """Сформировать текст категорий рынка"""
    return (
        '<tg-emoji emoji-id="5906909964328245730">🗓</tg-emoji> Выбери категорию на рынке:\n\n'
        '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji>Продажа ресурсов <tg-emoji emoji-id="6284888960644682300">🥕</tg-emoji>\n'
        '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji>Расходники <tg-emoji emoji-id="5334859426178313935">📕</tg-emoji>\n'
        '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji>Предметы <tg-emoji emoji-id="5936238625250350064">🎁</tg-emoji>'
    )

def _get_market_text(player: dict) -> str:
    """Сформировать текст страницы продажи ресурсов"""
    nickname = html.escape(player['nickname'])
    lines = [
        f"{E_MARKET} <b>РЫНОК</b> | Продажа ресурсов.\n",
        f"{nickname}, курс ресурсов:\n",
        f"{E_TRASH} | Продажа:",
        f"{E_FOOD} Еда | {MARKET_PRICES['food']}{E_COINS}",
        f"{E_WOOD} Древесина | {MARKET_PRICES['wood']}{E_COINS}",
        f"{E_STONE} Камень | {MARKET_PRICES['stone']}{E_COINS}",
        f"{E_IRON} Железо | {MARKET_PRICES['iron']}{E_COINS}",
        f"{E_GOLD_M} Золото | {MARKET_PRICES['gold']}{E_COINS}",
    ]
    return "\n".join(lines)

def _get_consumables_text(player: dict) -> str:
    """Сформировать текст страницы расходников"""
    nickname = html.escape(player['nickname'])
    return (
        f'{E_CHART} <b>РАСХОДНИКИ</b>\n\n'
        f'{nickname}, доступные расходники:\n\n'
        f'{E_TICKET} Билет рейда | {MARKET_RAID_TICKET_PRICE}{E_COINS}\n'
        f'Билетов у тебя: {player["raid_tickets"]} {E_TICKET}'
    )

@router.message(F.text == "🛒 Рынок")
async def open_market(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    await state.set_state(MarketMenu.viewing_category)
    await send_image_with_text(message, "images/rynokcategory.png", _get_market_category_text(), reply_markup=get_market_category_kb())

@router.message(MarketMenu.viewing_category)
async def handle_market_category(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    if text == "⬅️ Назад в меню":
        await show_main_menu(message, state)
        return

    if text == "🥕 Продажа ресурсов":
        await state.set_state(MarketMenu.viewing_market)
        await send_image_with_text(message, "images/rynok.png", _get_market_text(player), reply_markup=get_market_kb())
        return

    if text == "📕 Расходники":
        await state.set_state(MarketMenu.viewing_consumables)
        await message.answer(_get_consumables_text(player), reply_markup=get_consumables_kb(), parse_mode="HTML")
        return

    if text == "🎁 Предметы":
        await state.set_state(MarketMenu.viewing_items)
        items_text = _get_items_text(user_id)
        await message.answer(items_text, reply_markup=_get_items_kb(user_id), parse_mode="HTML")
        return

    # Fallback
    await send_image_with_text(message, "images/rynokcategory.png", _get_market_category_text(), reply_markup=get_market_category_kb())

@router.message(MarketMenu.viewing_market)
async def handle_market(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    if text == "⬅️ Назад к категориям":
        await state.set_state(MarketMenu.viewing_category)
        await send_image_with_text(message, "images/rynokcategory.png", _get_market_category_text(), reply_markup=get_market_category_kb())
        return

    # Check each sell button (plain emoji buttons)
    if text in _MARKET_SELL_BUTTONS:
        mat_key = _MARKET_SELL_BUTTONS[text]
        emoji, mat_name, _ = _MARKET_MAT_INFO[mat_key]
        inv = get_inventory(user_id)
        amount = inv.get(mat_key, 0)
        price = MARKET_PRICES[mat_key]
        if amount == 0:
            await message.answer(
                f"{E_CROSS} У тебя нет {emoji} {mat_name} для продажи!",
                reply_markup=get_market_kb()
            )
            return
        sell_text = (
            f"{emoji} <b>{mat_name}</b>\n\n"
            f"Доступно: {amount}\n"
            f"Цена: {price}{E_COINS} за единицу\n\n"
            f"Сколько хочешь продать?"
        )
        await state.update_data(sell_material=mat_key)
        await state.set_state(MarketMenu.selling_resource)
        await message.answer(sell_text, reply_markup=get_sell_qty_kb(mat_key, amount))
        return

    # Fallback: refresh market
    await send_image_with_text(message, "images/rynok.png", _get_market_text(player), reply_markup=get_market_kb())

@router.message(MarketMenu.selling_resource)
async def handle_market_sell(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    player = get_player(user_id)
    data = await state.get_data()
    mat_key = data.get('sell_material')

    if not player or not mat_key:
        await state.set_state(MarketMenu.viewing_market)
        await message.answer("Произошла ошибка. Вернулись на рынок.", reply_markup=get_market_kb())
        return

    if text == "⬅️ Назад на рынок":
        await state.set_state(MarketMenu.viewing_market)
        await send_image_with_text(message, "images/rynok.png", _get_market_text(player), reply_markup=get_market_kb())
        return

    emoji, mat_name, _ = _MARKET_MAT_INFO[mat_key]
    inv = get_inventory(user_id)
    current_amount = inv.get(mat_key, 0)
    price = MARKET_PRICES[mat_key]

    # Parse quantity from button text
    qty = None
    if text.startswith("Продать всё (") and text.endswith(")"):
        try:
            qty = int(text[len("Продать всё ("):-1])
        except ValueError:
            pass
    elif text.startswith("Продать "):
        try:
            qty = int(text[len("Продать "):])
        except ValueError:
            pass

    if qty is None or qty <= 0:
        await message.answer(
            "Выбери количество из кнопок ниже!",
            reply_markup=get_sell_qty_kb(mat_key, current_amount)
        )
        return

    if qty > current_amount:
        await message.answer(
            f"{E_CROSS} Недостаточно {emoji} {mat_name}!\nДоступно: {current_amount}",
            reply_markup=get_sell_qty_kb(mat_key, current_amount)
        )
        return

    # Calculate earnings (round to avoid floating point noise)
    earned = round(qty * price, 2)

    ok = remove_inventory_material(user_id, mat_key, qty)
    if not ok:
        await message.answer(
            f"{E_CROSS} Ошибка при продаже. Попробуй снова.",
            reply_markup=get_sell_qty_kb(mat_key, current_amount)
        )
        return

    add_coins_to_player(user_id, earned)
    updated = get_player(user_id)
    updated_inv = get_inventory(user_id)
    await message.answer(
        f"{E_PLUS} Продано: {qty} {emoji} {mat_name}\n"
        f"{E_PLUS} Получено: {earned}{E_COINS}\n\n"
        f"Монет теперь: {updated['coins']}{E_COINS}\n"
        f"Осталось {emoji}: {updated_inv[mat_key]}",
        reply_markup=get_sell_qty_kb(mat_key, updated_inv[mat_key])
    )
    # Keep state in selling_resource with updated inventory
    await state.update_data(sell_material=mat_key)

@router.message(MarketMenu.viewing_consumables)
async def handle_consumables(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    if text == "⬅️ Назад к категориям":
        await state.set_state(MarketMenu.viewing_category)
        await send_image_with_text(message, "images/rynokcategory.png", _get_market_category_text(), reply_markup=get_market_category_kb())
        return

    ticket_btn = f"Купить билет рейда ({MARKET_RAID_TICKET_PRICE}💰)"
    if text == ticket_btn:
        if player['coins'] < MARKET_RAID_TICKET_PRICE:
            await message.answer(
                f"{E_CROSS} Недостаточно монет!\n"
                f"Нужно: {MARKET_RAID_TICKET_PRICE}{E_COINS}\n"
                f"У тебя: {player['coins']}{E_COINS}",
                reply_markup=get_consumables_kb()
            )
            return
        remove_coins_from_player(user_id, MARKET_RAID_TICKET_PRICE)
        add_raid_tickets_to_player(user_id, 1)
        updated = get_player(user_id)
        await message.answer(
            f"{E_PLUS} Куплен {E_TICKET} Билет рейда!\n\n"
            f"- {MARKET_RAID_TICKET_PRICE}{E_COINS}\n"
            f"Теперь билетов: {updated['raid_tickets']} {E_TICKET}",
            reply_markup=get_consumables_kb()
        )
        return

    # Fallback
    await message.answer(_get_consumables_text(player), reply_markup=get_consumables_kb(), parse_mode="HTML")

@router.message(MarketMenu.viewing_items)
async def handle_items(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅️ Назад к категориям":
        player = get_player(user_id)
        await state.set_state(MarketMenu.viewing_category)
        await send_image_with_text(message, "images/rynokcategory.png", _get_market_category_text(), reply_markup=get_market_category_kb())
        return

    # Handle axe purchase
    for axe_id, axe_data in AXES.items():
        btn_text = f"🛒 Купить 🪓 ур.{axe_id} ({axe_data['cost']}👛)"
        if text == btn_text:
            player = get_player(user_id)
            if not player:
                await message.answer("Сначала зарегистрируйся! /start")
                return
            current_axe = get_player_axe_level(user_id)
            if current_axe >= axe_id:
                await message.answer(
                    f"{E_CROSS} Топор 🪓 {axe_id} level уже куплен!",
                    reply_markup=_get_items_kb(user_id), parse_mode="HTML"
                )
                return
            # Calculate total cost (buy all levels up to axe_id)
            total_cost = 0
            for lvl in range(current_axe + 1, axe_id + 1):
                total_cost += AXES[lvl]['cost']
            if player['coins'] < total_cost:
                await message.answer(
                    f"{E_CROSS} Недостаточно монет!\nТребуется: {total_cost}{E_COINS}\nУ вас: {player['coins']}{E_COINS}",
                    reply_markup=_get_items_kb(user_id), parse_mode="HTML"
                )
                return
            remove_coins_from_player(user_id, total_cost)
            set_player_axe_level(user_id, axe_id)
            await message.answer(
                f"✅ Топор 🪓 {axe_id} level куплен и экипирован!\n- {total_cost}{E_COINS}",
                reply_markup=_get_items_kb(user_id), parse_mode="HTML"
            )
            return

    items_text = _get_items_text(user_id)
    await message.answer(items_text, reply_markup=_get_items_kb(user_id), parse_mode="HTML")


def _get_items_text(user_id: int) -> str:
    """Сформировать текст списка предметов (топоров)"""
    current_axe = get_player_axe_level(user_id)
    lines = [f"{E_ITEMS_STAR} Список предметов:\n"]
    for axe_id, axe_data in AXES.items():
        owned = "✅" if current_axe >= axe_id else "❌"
        lines.append(
            f"{E_SQ}Топор - 🪓 {axe_id} level {axe_data['star_emoji']}\n"
            f"├ добывает {axe_data['min_wood']}-{axe_data['max_wood']}🌳\n"
            f"├ в наличии {owned}\n"
            f"{E_CIRCLE}Цена - {axe_data['cost']}{E_COINS}\n"
        )
    return "\n".join(lines)

def _get_items_kb(user_id: int) -> ReplyKeyboardMarkup:
    """Клавиатура предметов (топоры)"""
    current_axe = get_player_axe_level(user_id)
    kb = []
    for axe_id, axe_data in AXES.items():
        if current_axe < axe_id:
            kb.append([KeyboardButton(text=f"🛒 Купить 🪓 ур.{axe_id} ({axe_data['cost']}👛)")])
    kb.append([KeyboardButton(text="⬅️ Назад к категориям")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ============== CLAN BOSS HANDLERS ==============

async def _open_clan_boss_menu(message, state: FSMContext, clan: dict, user_id: int):
    """Показать меню кланового босса"""
    clan_id = clan['clan_id']

    # Проверка уровня клана
    if clan['clan_level'] < 3:
        text = (
            f"{E_WARN} Клановый босс доступен с уровня 3!\n"
            f"{E_YELLOW} Повышать уровень клана может каждый игрок, находящийся в данном клане за почти любые действия."
        )
        await message.answer(text, reply_markup=get_clan_boss_back_kb())
        await state.set_state(ClanBossState.viewing_menu)
        await state.update_data(clan_boss_clan_id=clan_id)
        return

    # Проверить cooldown и возможно возродить босса
    check_and_respawn_clan_boss(clan_id)
    boss_data = get_clan_boss(clan_id)
    boss_cfg = CLAN_BOSSES_CONFIG.get(boss_data['boss_num'], CLAN_BOSSES_CONFIG[1])

    if boss_data['status'] == 'cooldown':
        remaining = get_clan_boss_remaining_cooldown(clan_id)
        text = (
            f"{E_BAN} Босс уже был побежден недавно!\n"
            f"{E_SQ}{E_WARN} Новый босс появится через {E_HOURGLASS}{remaining}\n\n"
            f"{E_GREEN} Пока идёт обновление босса, можете отдохнуть от процесса!"
        )
        try:
            photo = FSInputFile("images/clanboss.png")
            await message.answer_photo(photo, caption=text, reply_markup=get_clan_boss_back_kb())
        except Exception:
            await message.answer(text, reply_markup=get_clan_boss_back_kb())
        await state.set_state(ClanBossState.viewing_menu)
        await state.update_data(clan_boss_clan_id=clan_id)
        return

    # Проверить билеты
    tickets = get_clan_boss_tickets(user_id, clan_id)

    if tickets <= 0:
        text = (
            f"{E_CB_SKULL} КЛАНОВЫЙ БОСС:\n\n"
            f"{E_SQ}{E_CB_CROWN} Босс: {boss_cfg['name']}\n"
            f"{E_SQ}{E_YELLOW} Сила: {boss_cfg['strength']} {E_ATK}\n"
            f"{E_SQ}{E_YELLOW} Здоровье: {boss_data['current_health']} {E_ESWORD}\n"
            f"{E_SQ}{E_YELLOW} Урон: {boss_cfg['damage']} {E_DMG}\n\n"
            f"{E_CB_TICKET}{E_BAN} У тебя закончились билеты!\n"
            f"{E_YELLOW} Они обновляются каждый час (по +3 билета)"
        )
        try:
            photo = FSInputFile("images/clanboss.png")
            await message.answer_photo(photo, caption=text, reply_markup=get_clan_boss_back_kb())
        except Exception:
            await message.answer(text, reply_markup=get_clan_boss_back_kb())
        await state.set_state(ClanBossState.viewing_menu)
        await state.update_data(clan_boss_clan_id=clan_id)
        return

    text = (
        f"{E_CB_SKULL} КЛАНОВЫЙ БОСС:\n\n"
        f"{E_SQ}{E_CB_CROWN} Босс: {boss_cfg['name']}\n"
        f"{E_SQ}{E_YELLOW} Сила: {boss_cfg['strength']} {E_ATK}\n"
        f"{E_SQ}{E_YELLOW} Здоровье: {boss_data['current_health']} {E_ESWORD}\n"
        f"{E_SQ}{E_YELLOW} Урон: {boss_cfg['damage']} {E_DMG}\n\n"
        f"{E_CB_CROWN}{E_CB_TICKET} Твои билеты: {tickets} / {MAX_CLAN_BOSS_TICKETS}"
    )
    try:
        photo = FSInputFile("images/clanboss.png")
        await message.answer_photo(photo, caption=text, reply_markup=get_clan_boss_menu_kb())
    except Exception:
        await message.answer(text, reply_markup=get_clan_boss_menu_kb())
    await state.set_state(ClanBossState.viewing_menu)
    await state.update_data(clan_boss_clan_id=clan_id)


@router.message(ClanBossState.viewing_menu)
async def handle_clan_boss_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_boss_clan_id')

    if text == "🔙 Назад":
        clan = get_player_clan(user_id)
        if clan:
            is_leader = (clan['leader_id'] == user_id)
            is_co_leader = not is_leader and get_clan_member_role(user_id, clan['clan_id']) == 'co_leader'
            await _show_clan_info(message, clan, is_leader, is_co_leader)
            await state.set_state(ClanMenu.viewing_my_clan)
            await state.update_data(clan_id=clan['clan_id'])
        else:
            await show_main_menu(message, state)
        return

    if text == "⚔️ помочь одолеть босса":
        if not clan_id:
            await show_main_menu(message, state)
            return

        # Проверить cooldown
        check_and_respawn_clan_boss(clan_id)
        boss_data = get_clan_boss(clan_id)
        if boss_data['status'] == 'cooldown':
            remaining = get_clan_boss_remaining_cooldown(clan_id)
            await message.answer(
                f"{E_BAN} Босс уже был побежден недавно!\n"
                f"{E_SQ}{E_WARN} Новый босс появится через {E_HOURGLASS}{remaining}"
            )
            return

        # Проверить билеты
        tickets = get_clan_boss_tickets(user_id, clan_id)
        if tickets <= 0:
            await message.answer(
                f"{E_CB_TICKET}{E_BAN} У тебя закончились билеты!\n"
                f"{E_YELLOW} Они обновляются каждый час (по +3 билета)"
            )
            return

        # Начать бой
        player = get_player(user_id)
        if not player:
            await show_main_menu(message, state)
            return

        boss_cfg = CLAN_BOSSES_CONFIG.get(boss_data['boss_num'], CLAN_BOSSES_CONFIG[1])
        clan = get_player_clan(user_id)
        clan_level = clan['clan_level'] if clan else 1
        buffed_strength = apply_clan_strength_buff(player['strength'], clan_level)
        player_health = calculate_player_health(buffed_strength)
        player_damage = calculate_damage(buffed_strength)

        reset_battle_cooldown(user_id)

        await state.set_state(ClanBossState.battle_round)
        await state.update_data(
            clan_boss_clan_id=clan_id,
            clan_boss_num=boss_data['boss_num'],
            cb_player_health=player_health,
            cb_player_damage=player_damage,
            cb_boss_health=boss_data['current_health'],
            cb_boss_damage=boss_cfg['damage'],
            cb_damage_dealt=0,
            cb_player_mana=100,
            cb_boss_skip_turn=False,
            cb_boss_blind_turns=0,
        )

        battle_info = (
            f"{E_CB_SKULL} БОЙ С {boss_cfg['name'].upper()}!\n\n"
            f"{E_SQ}{E_YELLOW} Здоровье босса: {boss_data['current_health']} {E_ESWORD}\n"
            f"{E_SQ}{E_HP} Твоё здоровье: {player_health}\n"
            f"{E_SQ}{E_ATK} Твой урон: {player_damage}\n"
            f"{E_SQ}{E_MANA} Мана: 100/100\n\n"
            f"{E_HASHTAG} Атакуй!"
        )
        await message.answer(battle_info, reply_markup=get_clan_boss_battle_kb(user_id, 100))
        return

    clan = get_player_clan(user_id)
    if clan:
        await _open_clan_boss_menu(message, state, clan, user_id)


@router.message(ClanBossState.battle_round)
async def handle_clan_boss_battle(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    clan_id = data.get('clan_boss_clan_id')
    boss_num = data.get('clan_boss_num', 1)
    player_health = data.get('cb_player_health', 1)
    player_damage = data.get('cb_player_damage', 1)
    boss_health = data.get('cb_boss_health', 1)
    boss_damage = data.get('cb_boss_damage', 1)
    damage_dealt_total = data.get('cb_damage_dealt', 0)
    mana = data.get('cb_player_mana', 100)
    boss_skip_turn = data.get('cb_boss_skip_turn', False)
    boss_blind_turns = data.get('cb_boss_blind_turns', 0)

    # Определить допустимые действия (атака + скиллы)
    valid_actions = {"⚔️ Атаковать"}
    for sk_id, sk in SKILLS.items():
        if has_purchased_skill(user_id, sk_id):
            valid_actions.add(f"✨ Скилл {sk_id}: {sk['name']}")

    if text not in valid_actions:
        await message.answer("Используй кнопки!", reply_markup=get_clan_boss_battle_kb(user_id, mana))
        return

    # Cooldown check
    if not can_battle_action(user_id):
        await message.answer("⏳ Подожди перед следующим ходом!")
        return

    boss_cfg = CLAN_BOSSES_CONFIG.get(boss_num, CLAN_BOSSES_CONFIG[1])
    player = get_player(user_id)
    new_mana = mana
    new_boss_skip = False
    new_boss_blind = max(0, boss_blind_turns - 1) if boss_blind_turns > 0 else 0
    new_player_health = player_health
    battle_log = ""

    # ---- Обработка действия игрока ----
    skill_used = None
    for sk_id, sk in SKILLS.items():
        if text == f"✨ Скилл {sk_id}: {sk['name']}":
            skill_used = (sk_id, sk)
            break

    if skill_used:
        sk_id, sk = skill_used
        if mana < sk['mana_cost']:
            await message.answer(
                f"{E_CROSS} Недостаточно маны! Требуется {sk['mana_cost']}{E_MANA}",
                reply_markup=get_clan_boss_battle_kb(user_id, mana)
            )
            return
        new_mana -= sk['mana_cost']
        battle_log += f"✨ {sk['name']}!\n"

        if roll_miss():
            battle_log += f"{E_CROSS}{E_ATK} Промах! Босс уклонился\n\n"
            player_hit = 0
        elif sk_id == 1:  # Мега-молот: урон + стан
            player_hit = int(round(player_damage * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            battle_log += f"{E_BELL}{E_DMG} Ты наносишь {player_hit} урона! {E_ARROW_UP}\n"
            if random.random() < sk['stun_chance']:
                new_boss_skip = True
                battle_log += "😵 Босс оглушён и пропустит следующий ход!\n"
        elif sk_id == 2:  # Кровавое неистовство: 2x урон, -15% HP
            player_hit = int(round(player_damage * sk['damage_mult'] * random.uniform(0.8, 1.2)))
            hp_loss = max(1, int(round(calculate_player_health(player['strength']) * sk['hp_loss_pct'])))
            new_player_health = max(1, new_player_health - hp_loss)
            battle_log += f"🩸 Вы теряете {hp_loss} HP!\n"
            battle_log += f"{E_BELL}{E_DMG} Ты наносишь {player_hit} урона! {E_ARROW_UP}\n"
        elif sk_id == 3:  # Ослепляющая вспышка: ослепление на 2 хода
            player_hit = 0
            new_boss_blind = sk['blind_turns']
            battle_log += f"🔦 Босс ослеплён на {sk['blind_turns']} хода! (-50% точности)\n"
        else:
            player_hit = int(round(player_damage * random.uniform(0.8, 1.2)))
            battle_log += f"{E_BELL}{E_DMG} Ты наносишь {player_hit} урона! {E_ARROW_UP}\n"
        battle_log += "\n"
    else:
        # Обычная атака
        if roll_miss():
            player_hit = 0
            battle_log = f"{E_CROSS}{E_ATK} Промах! Босс уклонился\n\n"
        else:
            player_hit = int(round(player_damage * random.uniform(0.8, 1.2)))
            battle_log = (
                f"{E_BELL}{E_DMG} Ты ударяешь!\n"
                f"{E_ARROW_UP}{E_ATK} Урон боссу: {player_hit}\n\n"
            )

    new_boss_health = max(0, boss_health - player_hit)
    new_damage_dealt = damage_dealt_total + player_hit

    # Проверка победы над боссом
    if new_boss_health <= 0:
        # Записать урон
        add_clan_boss_damage(user_id, clan_id, new_damage_dealt)
        # Обновить здоровье босса в DB
        boss_data_db = get_clan_boss(clan_id)
        if boss_data_db['status'] == 'active':
            final_health = max(0, boss_data_db['current_health'] - new_damage_dealt)
            if final_health <= 0:
                # Босс побеждён!
                use_clan_boss_ticket(user_id, clan_id)
                await _handle_clan_boss_victory(message, state, clan_id, boss_num, boss_cfg, player, user_id)
                return
            else:
                update_clan_boss_health(clan_id, final_health)

        # Другой игрок уже убил босса, пока мы воевали
        use_clan_boss_ticket(user_id, clan_id)
        await message.answer(
            f"{E_BAN} Босс уже был побеждён другим игроком клана!",
            reply_markup=get_clan_boss_back_kb()
        )
        await state.set_state(ClanBossState.viewing_menu)
        return

    # Босс атакует игрока
    if boss_skip_turn:
        battle_log += f"😵 {boss_cfg['name']} оглушён, пропускает ход!\n\n"
        boss_hit = 0
    else:
        # Учитываем ослепление босса
        miss_chance = 0.1
        if boss_blind_turns > 0:
            miss_chance += SKILLS[3]['miss_chance_add']
        if random.random() < miss_chance:
            boss_hit = 0
            battle_log += f"{E_CROSS}{E_ATK} {boss_cfg['name']} промахивается!\n\n"
        else:
            boss_hit = int(round(boss_damage * random.uniform(0.8, 1.2)))
            battle_log += (
                f"{E_ARROW_DN}{E_ESWORD} {boss_cfg['name']} атакует!\n"
                f"{E_HEART_B} Урон тебе: {boss_hit}\n\n"
            )

    new_player_health = max(0, new_player_health - boss_hit)

    battle_log += (
        f"{E_HP} Твоё здоровье: {new_player_health}\n"
        f"{E_MANA} Мана: {new_mana}/100\n"
        f"{E_ESWORD} Здоровье босса: {new_boss_health}\n"
    )

    # Проверка поражения игрока
    if new_player_health <= 0:
        # Записать урон
        if new_damage_dealt > 0:
            add_clan_boss_damage(user_id, clan_id, new_damage_dealt)
            boss_data_db = get_clan_boss(clan_id)
            if boss_data_db['status'] == 'active':
                final_health = max(0, boss_data_db['current_health'] - new_damage_dealt)
                update_clan_boss_health(clan_id, final_health)

        use_clan_boss_ticket(user_id, clan_id)
        defeat_text = (
            f"{E_CB_DOWN} ВЫ ПРОИГРАЛИ!\n"
            f"{E_SQ}{E_CB_STAR} Но вы внесли свой урон в босса!\n\n"
            f"{E_SQ}Вы нанесли в целом урона: {new_damage_dealt} {E_DMG}\n\n"
            f"{E_CB_CROWN}{E_CB_SKULL} Ты был повержен {boss_cfg['name']}...\n\n"
            f"{E_CROSS} -1 {E_CB_TICKET} билет потрачен"
        )
        await message.answer(battle_log + "\n" + defeat_text, reply_markup=get_clan_boss_back_kb())
        await state.set_state(ClanBossState.viewing_menu)
        await state.update_data(clan_boss_clan_id=clan_id)
        return

    # Продолжение боя
    await state.update_data(
        cb_player_health=new_player_health,
        cb_boss_health=new_boss_health,
        cb_damage_dealt=new_damage_dealt,
        cb_player_mana=new_mana,
        cb_boss_skip_turn=new_boss_skip,
        cb_boss_blind_turns=new_boss_blind,
    )
    await message.answer(battle_log, reply_markup=get_clan_boss_battle_kb(user_id, new_mana))


async def _handle_clan_boss_victory(message, state: FSMContext, clan_id: int, boss_num: int,
                                    boss_cfg: dict, player: dict, user_id: int):
    """Обработать победу над клановым боссом"""
    # Получить всех участников ДО удаления записей об уроне
    participants = get_clan_boss_participants(clan_id)

    # Если убийца не попал в список участников (нанёс урон только в этом ходу)
    if user_id not in participants:
        participants.append(user_id)

    defeat_clan_boss(clan_id, boss_num)

    # Время до следующего босса
    next_boss_num = 2 if boss_num == 1 else 1
    next_cfg = CLAN_BOSSES_CONFIG.get(next_boss_num, CLAN_BOSSES_CONFIG[1])
    cooldown_text = f"{next_cfg['cooldown_minutes']} мин"

    # Начислить опыт клану один раз
    exp_clan = boss_cfg['rewards']['exp_clan']
    add_clan_exp(clan_id, exp_clan)

    # Начислить и уведомить каждого участника
    for participant_uid in participants:
        p = get_player(participant_uid)
        if not p:
            continue

        p_crystals = boss_cfg['rewards']['crystals_base']
        if random.random() < boss_cfg['rewards']['crystals_bonus_chance']:
            p_crystals += boss_cfg['rewards']['crystals_bonus']
        p_coins = _get_boss_coins_reward(p['strength'], boss_cfg)
        p_exp_profile = random.randint(*boss_cfg['rewards']['exp_profile'])
        p_rating = boss_cfg['rewards']['rating']

        add_crystals_to_player(participant_uid, p_crystals)
        add_coins_to_player(participant_uid, p_coins)
        add_experience_to_player(participant_uid, p_exp_profile)
        update_rating_points(participant_uid, p_rating)

        p_victory_text = (
            f"{E_SQ}{E_CB_CROWN} БОСС КЛАНА ПОВЕРЖЕН!\n\n"
            f"{E_CB_SKULL} {boss_cfg['name']} был убит! {E_CB_DOWN}\n\n"
            f"{E_GIFT}  Награда получена:\n"
            f"{E_PLUS} {p_crystals} {E_CRYSTALS} кристаллов\n"
            f"{E_PLUS} {p_coins} {E_COINS} монет\n"
            f"{E_PLUS} {p_exp_profile} {E_EXP} опыта профиля\n"
            f"{E_PLUS} {exp_clan} {E_CLAN_BOTTLE} опыта клана\n"
            f"{E_PLUS} {p_rating} 💠 очков рейтинга\n\n"
            f"{E_SQ}{E_WARN} Новый босс появится через {E_HOURGLASS}{cooldown_text}\n"
            f"{E_ONLINE2} Благодарность всем игрокам за помощь!"
        )

        if participant_uid == user_id:
            await message.answer(p_victory_text, reply_markup=get_clan_boss_back_kb())
            await state.set_state(ClanBossState.viewing_menu)
            await state.update_data(clan_boss_clan_id=clan_id)
        else:
            try:
                await bot.send_message(chat_id=participant_uid, text=p_victory_text)
            except Exception:
                pass


async def clan_boss_ticket_refresh_loop():
    """Фоновая задача: каждый час обновляет билеты кланового босса"""
    while True:
        await asyncio.sleep(TICKET_REFRESH_INTERVAL_SECONDS)
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            # Найти всех игроков с меньше 3 билетами
            cursor.execute('SELECT user_id, clan_id, tickets FROM clan_boss_tickets WHERE tickets < 3')
            rows = cursor.fetchall()
            conn.close()

            for uid, cid, current_tickets in rows:
                # Восстановить до 3 билетов
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE clan_boss_tickets SET tickets = ?, last_refresh = CURRENT_TIMESTAMP WHERE user_id = ? AND clan_id = ?',
                    (MAX_CLAN_BOSS_TICKETS, uid, cid)
                )
                conn.commit()
                conn.close()

                # Уведомить игрока
                try:
                    await bot.send_message(
                        chat_id=uid,
                        text=(
                            f"{E_SQ}{E_ARROW_UP} Билеты для атаки босса обновились!\n\n"
                            f"{E_GIFT} Получено:\n"
                            f"{E_PLUS} 3 {E_CB_TICKET} билета"
                        )
                    )
                except Exception:
                    pass
        except Exception as e:
            logging.warning(f"clan_boss_ticket_refresh_loop error: {e}")

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.states import ProfileMenu
from bot.database import (
    get_player, get_experience_progress, get_player_weapon, get_player_armor,
    get_player_clan, get_player_with_chest_statuses,
    set_player_status, set_player_block_invites,
)
from bot.utils import (
    apply_clan_strength_buff, calculate_player_health,
    send_image_with_text, safe_html_answer, format_profile_text,
)
from bot.keyboards import get_profile_kb, get_statuses_kb, show_main_menu
from bot.data.equipment import DEFAULT_WEAPON, DEFAULT_ARMOR
from bot.data.statuses import STATUSES, is_status_available, _format_statuses_text, _get_status_requirement_text
from bot.emojis import *
from bot.data.leagues_config import get_league_label

router = Router()


@router.message(Command("профиль"))
@router.message(F.text == "/профиль")
@router.message(F.text == "📖 Профиль")
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
    player_clan = get_player_clan(player['user_id'])
    clan_level = player_clan['clan_level'] if player_clan else 1
    display_strength = apply_clan_strength_buff(player['strength'], clan_level)
    health = calculate_player_health(display_strength)
    exp_info = get_experience_progress(player['user_id'])
    league = get_league_label(player.get('rating_points', 0))

    response = format_profile_text(
        nickname=player["nickname"],
        status=player["status"],
        level=player["player_level"],
        current_exp=exp_info["current_exp"],
        needed_exp=exp_info["needed_exp"],
        rating_points=player.get("rating_points", 0),
        league=league,
        wins=player["wins"],
        strength=int(display_strength),
        health=health,
        coins=player["coins"],
        crystals=player["crystals"],
        raid_tickets=player["raid_tickets"],
        likes=player.get("likes", 0),
    )
    await send_image_with_text(message, "images/profile.png", response, reply_markup=get_profile_kb())

@router.message(ProfileMenu.viewing_profile)
async def handle_profile_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "🏠 Назад":
        await show_main_menu(message, state)
        return

    if text == "📦 Инвентарь":
        from bot.handlers.all_handlers import _send_inventory
        await state.set_state(ProfileMenu.viewing_inventory)
        await state.update_data(inv_from_profile=True)
        await _send_inventory(message, user_id)
        return

    if text == "⚙️ Настройки":
        player = get_player(user_id)
        if player:
            await state.set_state(ProfileMenu.viewing_settings)
            await _send_settings(message, player)
        return

    if text == "🎭 Статусы":
        player = get_player_with_chest_statuses(user_id)
        await state.set_state(ProfileMenu.viewing_statuses)
        await state.update_data(statuses_page=0)
        statuses_text = _format_statuses_text(player, 0)
        await safe_html_answer(message, statuses_text, reply_markup=get_statuses_kb(player, 0))
        return

    # Refresh profile
    player = get_player(user_id)
    if player:
        await _send_profile(message, player)

@router.message(ProfileMenu.viewing_statuses)
async def handle_profile_statuses(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player_with_chest_statuses(user_id)
    text = message.text
    data = await state.get_data()
    current_page = data.get('statuses_page', 0)

    if text == "⬅️ Назад":
        await state.set_state(ProfileMenu.viewing_profile)
        await _send_profile(message, player)
        return

    if text == "След. страница ➡️":
        new_page = current_page + 1
        await state.update_data(statuses_page=new_page)
        statuses_text = _format_statuses_text(player, new_page)
        await safe_html_answer(message, statuses_text, reply_markup=get_statuses_kb(player, new_page))
        return

    if text == "⬅️ Пред. страница":
        new_page = max(0, current_page - 1)
        await state.update_data(statuses_page=new_page)
        statuses_text = _format_statuses_text(player, new_page)
        await safe_html_answer(message, statuses_text, reply_markup=get_statuses_kb(player, new_page))
        return

    # Check if player selected a status
    for s_id, s in STATUSES.items():
        can = is_status_available(player, s)
        owned = (player.get('status') == s['name'])
        label_base = f"{s['emoji']} {s['name']}"
        if text.startswith(label_base):
            if owned:
                await message.answer(f"✅ Статус «{s['name']}» уже активен!", reply_markup=get_statuses_kb(player, current_page))
                return
            if not can:
                req_text = _get_status_requirement_text(s)
                await message.answer(f"{req_text} — условие не выполнено!", reply_markup=get_statuses_kb(player, current_page))
                return
            set_player_status(user_id, s['name'])
            updated = get_player_with_chest_statuses(user_id)
            await message.answer(f"✅ Статус изменён на «{s['name']}» {s['emoji']}!", reply_markup=get_statuses_kb(updated, current_page))
            return

    await message.answer("Выбери статус из списка!", reply_markup=get_statuses_kb(player, current_page))


def _send_settings_text(player: dict) -> str:
    """Build the settings message text."""
    block_invites = bool(player.get('block_invites', 0))
    status_emoji = "✅" if block_invites else "❌"
    return (
        "⚙️ <b>Настройки бота:</b>\n\n"
        "🔒 Заблокировать приглашения в друзья от игроков и выключить оповещения:\n"
        "ℹ️ <i>Обычно это приглашения в рейд и т.д</i>\n"
        f"Статус: ({status_emoji})\n\n"
        "Нажми кнопку ниже, чтобы изменить настройку."
    )


def _get_settings_kb(block_invites: bool) -> ReplyKeyboardMarkup:
    label = "🔓 Включить приглашения" if block_invites else "🔒 Заблокировать приглашения"
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=label)],
        [KeyboardButton(text="⬅️ Назад в профиль")],
    ], resize_keyboard=True)


async def _send_settings(message, player: dict):
    """Отправить сообщение с настройками"""
    block_invites = bool(player.get('block_invites', 0))
    await message.answer(
        _send_settings_text(player),
        reply_markup=_get_settings_kb(block_invites),
        parse_mode="HTML"
    )


@router.message(ProfileMenu.viewing_settings)
async def handle_profile_settings(message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    player = get_player(user_id)

    if text == "⬅️ Назад в профиль" or text == "🏠 Назад":
        await state.set_state(ProfileMenu.viewing_profile)
        if player:
            await _send_profile(message, player)
        return

    if text in ("🔒 Заблокировать приглашения", "🔓 Включить приглашения"):
        if player:
            current = bool(player.get('block_invites', 0))
            new_val = not current
            set_player_block_invites(user_id, new_val)
            updated = get_player(user_id)
            if updated:
                await _send_settings(message, updated)
        return

    if player:
        await _send_settings(message, player)

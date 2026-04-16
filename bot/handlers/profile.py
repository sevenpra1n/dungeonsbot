from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import html

from bot.states import ProfileMenu
from bot.database import (
    get_player, get_experience_progress, get_player_weapon, get_player_armor,
    get_player_status_emoji, get_player_clan, get_player_with_chest_statuses,
    set_player_status,
)
from bot.utils import (
    apply_clan_strength_buff, calculate_player_health, calculate_damage,
    send_image_with_text, safe_html_answer,
)
from bot.keyboards import get_profile_kb, get_statuses_kb, show_main_menu
from bot.data.equipment import DEFAULT_WEAPON, DEFAULT_ARMOR
from bot.data.statuses import STATUSES, is_status_available, _format_statuses_text, _get_status_requirement_text
from bot.emojis import *
from bot.database import get_rating_league

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
    damage = calculate_damage(display_strength)
    exp_info = get_experience_progress(player['user_id'])
    status_emoji = get_player_status_emoji(player)
    league = get_rating_league(player.get('rating_points', 0))

    safe_nick = html.escape(player["nickname"])
    safe_status = html.escape(player["status"])
    response = (
        f'{E_PROFILE} Профиль {safe_nick}:\n'
        f'{E_LOCK}{E_HASHTAG} {safe_nick}\n\n'
        f'{status_emoji} {safe_status}\n\n'
        f'Уровень {E_CIRCLE} {player["player_level"]}{E_STAR}\n'
        f'{E_SQ}{exp_info["current_exp"]} / {exp_info["needed_exp"]}{E_EXP_DOT}{E_EXP} Опыта\n\n'
        f'Рейтинговая лига:\n'
        f'{E_SQ}{player.get("rating_points", 0)} {E_STAR} Points\n'
        f'{E_SQ}{league}\n\n'
        f'{E_SQ}{player["wins"]} - {E_TROPHY} {E_YELLOW} Победы\n'
        f'{E_SQ}{int(display_strength)} - {E_ATK} {E_YELLOW} Сила\n'
        f'{E_SQ}{health} - {E_HP} {E_YELLOW} Здоровье\n\n'
        f'{E_SQ}{player["coins"]} - {E_COINS}{E_GREEN} Монеты  \n'
        f'{E_SQ}{player["crystals"]} - {E_CRYSTALS}{E_GREEN} Кристаллы  \n'
        f'{E_SQ}{player["raid_tickets"]} - {E_TICKET}{E_GREEN} Билеты рейда\n\n'
        f'{E_SQ}{E_HP} {player.get("likes", 0)} лайков профиля\n'
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
        from bot.handlers.inventory import _send_inventory
        await state.set_state(ProfileMenu.viewing_inventory)
        await state.update_data(inv_from_profile=True)
        await _send_inventory(message, user_id)
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

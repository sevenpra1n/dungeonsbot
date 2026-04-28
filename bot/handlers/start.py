import asyncio
import random

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.states import Registration, TutorialState, ProfileMenu
from bot.database import get_player, add_player, add_inventory_material
from bot.utils import send_image_with_text
from bot.keyboards import show_main_menu, get_main_menu_text, get_main_kb
from bot.emojis import (
    E_PROFILE, E_SQ, E_GIFT, E_CROSS, E_COINS, E_CRYSTALS,
    E_WARN, E_EXP, E_PLUS, E_BELL, E_SWORD, E_STAR, E_TROPHY,
    E_CROWN, E_INV_BOX, E_WOOD, E_STONE, E_FOOD, E_IRON,
    E_GOLD_M, E_COPPER, E_CHEST_W,
)

router = Router()

RANDOM_NICKNAMES = [
    "ShadowKnight", "IronFox", "StormBlade",
    "DarkRaven", "GoldArrow", "FrostWolf",
    "BlazeSword", "NightHawk", "CrimsonAce",
    "VoidHunter", "StoneBreaker", "SilverEdge",
]


def _get_random_nicknames(n: int = 6) -> list[str]:
    return random.sample(RANDOM_NICKNAMES, min(n, len(RANDOM_NICKNAMES)))


def _get_nickname_kb(suggestions: list[str]) -> ReplyKeyboardMarkup:
    """Клавиатура с кнопками случайных никнеймов (по 2 в ряд)"""
    rows = []
    for i in range(0, len(suggestions), 2):
        row = [KeyboardButton(text=suggestions[i])]
        if i + 1 < len(suggestions):
            row.append(KeyboardButton(text=suggestions[i + 1]))
        rows.append(row)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)

    if player:
        await show_main_menu(message, state)
    else:
        welcome_text = (
            f"{E_CROWN} Приветствую тебя в моём боте <b>\"Hades\"</b>!\n"
            f" {E_SWORD} Желаешь начать игру?\n"
            f"{E_STAR}Я введу тебя в курс дела, и всё объясню кратко!"
        )
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Давай начнём!")]],
            resize_keyboard=True
        )
        await send_image_with_text(message, "images/privetstvie.png", welcome_text, reply_markup=kb)
        await state.set_state(TutorialState.welcome)


@router.message(TutorialState.welcome)
async def tutorial_welcome_response(message: types.Message, state: FSMContext):
    if message.text != "Давай начнём!":
        return
    suggestions = _get_random_nicknames(6)
    await state.update_data(nick_suggestions=suggestions)
    ask_nick_text = (
        f"{E_PROFILE} Отлично! Как тебя звать?\n"
        f"{E_SQ}до 30 символов максимум."
    )
    await message.answer(ask_nick_text, reply_markup=_get_nickname_kb(suggestions), parse_mode="HTML")
    await state.set_state(TutorialState.entering_nickname)


@router.message(TutorialState.entering_nickname)
async def tutorial_process_nickname(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    nickname = message.text.strip() if message.text else ""

    if not nickname or len(nickname) > 30:
        await message.answer(
            f"{E_CROSS} Никнейм должен быть от 1 до 30 символов. Попробуй ещё раз:",
            parse_mode="HTML"
        )
        return

    add_player(user_id, nickname)

    confirm_text = (
        f"{E_BELL} Никнейм успешно выбран!\n"
        f"Тебя зовут <b>{nickname}</b>, красивое название."
    )
    await message.answer(confirm_text, reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True), parse_mode="HTML")
    await asyncio.sleep(2)

    # Tutorial: show inventory
    from bot.database import get_inventory
    from bot.data.inventory_config import format_inventory_text
    from bot.utils import md_escape
    from bot.data.emojis import MD_INV_HEADER

    inv = get_inventory(user_id)
    inv_text = (
        f'{MD_INV_HEADER} \\| Инвентарь {md_escape(nickname)}:\n'
        + format_inventory_text(inv)
        + "\n\n"
        + r"\📦 *Инвентарь* — здесь хранятся все ресурсы которые ты добываешь\."
        + "\n"
        + r"Монеты, древесина, камень, руда — всё идёт сюда\."
        + "\n"
        + r"Компоненты нужны для крафта предметов в Кузне\."
        + "\n"
        + r"Сундуки — открой, чтобы получить награды\!"
    )
    no_kb = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
    await send_image_with_text(message, "images/inventory.png", inv_text, reply_markup=no_kb, parse_mode="MarkdownV2")
    await asyncio.sleep(4)

    # Tutorial: show profile
    from bot.database import get_experience_progress, get_player_clan
    from bot.utils import apply_clan_strength_buff, calculate_player_health, format_profile_text
    from bot.data.leagues_config import get_league_label

    player = get_player(user_id)
    if player:
        player_clan = get_player_clan(user_id)
        clan_level = player_clan['clan_level'] if player_clan else 1
        display_strength = apply_clan_strength_buff(player['strength'], clan_level)
        health = calculate_player_health(display_strength)
        exp_info = get_experience_progress(user_id)
        league = get_league_label(player.get('rating_points', 0))

        profile_text = format_profile_text(
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
        profile_explain = (
            profile_text
            + f"\n\n{E_CROWN} <b>Профиль</b> — твоя карточка игрока.\n"
            + f"{E_COINS} <b>Монеты</b> — основная валюта для улучшений.\n"
            + f"{E_CRYSTALS} <b>Кристаллы</b> — премиум валюта для особых возможностей.\n"
            + f"{E_STAR} <b>Уровень и опыт</b> — растут за любые действия в игре.\n"
            + f"{E_TROPHY} <b>Победы</b> — считаются за всех побеждённых врагов."
        )
        await send_image_with_text(message, "images/profile.png", profile_explain, reply_markup=no_kb)
        await asyncio.sleep(4)

    # Give reward: +1 wooden chest
    add_inventory_material(user_id, 'chest_wood', 1)

    reward_text = (
        f"{E_GIFT} Спасибо что выбрал мой бот!\n\n"
        f"Желаю тебе удачи в своих приключениях! {E_SWORD}\n\n"
        f"{E_PLUS} Награда за начало игры:\n"
        f"{E_CHEST_W} +1 Деревянный сундук"
    )
    await message.answer(reward_text, parse_mode="HTML")
    await asyncio.sleep(2)

    await state.clear()
    await send_image_with_text(message, "images/menu.png", get_main_menu_text(), reply_markup=get_main_kb())

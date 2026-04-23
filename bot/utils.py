"""Utility functions: battle calculations, message sending helpers."""

import os
import re
import random
import html
from datetime import datetime

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile

from bot.data.enemies import ENEMIES
from bot.data.clans import CLAN_BUFFS
from bot.global_state import battle_cooldowns, image_file_id_cache
from bot.emojis import (
    E_PROFILE, E_HASHTAG, E_CIRCLE, E_EXP_DOT,
    E_TROPHY, E_ATK, E_HP, E_COINS, E_CRYSTALS, E_TICKET,
)
from bot.data.emojis import E_LEAGUE_POINTS, E_LIKE_THUMB


# ============== BATTLE CALCULATIONS ==============

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


def _get_status_emoji(status_name: str) -> str:
    """Получить custom emoji статуса по его имени."""
    from bot.data.statuses import STATUSES
    for s in STATUSES.values():
        if s['name'] == status_name:
            return s.get('custom_emoji', '')
    return ''


def format_profile_text(
    nickname: str,
    status: str,
    level: int,
    current_exp: int,
    needed_exp: int,
    rating_points: int,
    league: str,
    wins: int,
    strength: int,
    health: int,
    coins: int,
    crystals: int,
    raid_tickets: int,
    likes: int,
) -> str:
    """Сформировать единый текст профиля с эмодзи."""
    safe_nick = html.escape(str(nickname))
    safe_status = html.escape(str(status))
    status_emoji = _get_status_emoji(status)
    return (
        f'{E_PROFILE} Профиль {safe_nick}:\n'
        f'{E_HASHTAG} {safe_nick}\n\n'
        f'{status_emoji} {safe_status}\n\n'
        f'{E_CIRCLE} Уровень  {int(level)}\n'
        f'{E_EXP_DOT} {int(current_exp)} / {int(needed_exp)} Опыта\n\n'
        f'Рейтинговая лига:\n'
        f'{E_LEAGUE_POINTS} {int(rating_points)}  Points\n'
        f'{league}\n\n'
        f'{E_TROPHY} {int(wins)} -   Победы\n'
        f'{E_ATK} {int(strength)} -   Сила\n'
        f'{E_HP} {int(health)} -   Здоровье\n\n'
        f'{E_COINS} {int(coins)} -  Монеты  \n'
        f'{E_CRYSTALS} {int(crystals)} -  Кристаллы  \n'
        f'{E_TICKET} {int(raid_tickets)} -  Билеты рейда\n\n'
        f'{E_LIKE_THUMB} {int(likes)} лайков профиля\n'
    )


# ============== MESSAGE SENDING HELPERS ==============

# Regex to strip <tg-emoji ...>fallback</tg-emoji> → fallback character
_TG_EMOJI_RE = re.compile(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', re.DOTALL)


def _strip_tg_emoji(text: str) -> str:
    """Убрать tg-emoji HTML-теги, оставив только символ-замену."""
    return _TG_EMOJI_RE.sub(r'\1', text)


async def safe_html_answer(message, text: str, **kwargs):
    """Отправить HTML-сообщение. При DOCUMENT_INVALID автоматически убирает кастомные эмодзи и повторяет."""
    try:
        return await message.answer(text, parse_mode="HTML", **kwargs)
    except TelegramBadRequest as e:
        if "DOCUMENT_INVALID" in str(e):
            return await message.answer(_strip_tg_emoji(text), parse_mode="HTML", **kwargs)
        raise


async def send_image_with_text(message, image_path: str, text: str, reply_markup=None):
    """Отправить изображение с текстом. Если файл не найден — отправить только текст."""
    async def _send_photo(caption: str):
        cached_id = image_file_id_cache.get(image_path)
        photo = cached_id if cached_id else FSInputFile(image_path)
        result = await message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        if not cached_id and result and result.photo:
            image_file_id_cache[image_path] = result.photo[-1].file_id

    try:
        if not os.path.exists(image_path):
            print(f"⚠️ ФАЙЛ НЕ НАЙДЕН: {image_path}")
            await safe_html_answer(message, text, reply_markup=reply_markup)
            return
        try:
            await _send_photo(text)
        except TelegramBadRequest as e:
            if "DOCUMENT_INVALID" in str(e):
                # Retry with plain emoji fallback
                try:
                    await _send_photo(_strip_tg_emoji(text))
                except Exception:
                    await message.answer(_strip_tg_emoji(text), reply_markup=reply_markup, parse_mode="HTML")
            else:
                await safe_html_answer(message, text, reply_markup=reply_markup)
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        await safe_html_answer(message, text, reply_markup=reply_markup)

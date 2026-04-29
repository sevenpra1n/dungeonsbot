"""Ban check middleware — intercepts messages from banned players."""

from typing import Callable, Any, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from bot.config import ADMIN_IDS
from bot.database import is_player_banned, get_player, get_player_ban, format_ban_remaining
from bot.keyboards import get_ban_appeal_kb

# Callbacks that should pass through even when banned
_ALLOWED_CALLBACKS = {"appeal_ban", "warn_ack"}

_E_YELLOW   = '<tg-emoji emoji-id="5906800644525660990">🟡</tg-emoji>'
_E_RED      = '<tg-emoji emoji-id="5907027122446145395">🔴</tg-emoji>'
_E_UNLOCK   = '<tg-emoji emoji-id="5429405838345265327">🔓</tg-emoji>'
_E_MEGA     = '<tg-emoji emoji-id="5278528159837348960">📢</tg-emoji>'
_E_HOUR     = '<tg-emoji emoji-id="5287579571485422439">⏳</tg-emoji>'
_E_CLOCK    = '<tg-emoji emoji-id="5276412364458059956">🕓</tg-emoji>'
_E_MARKER   = '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji>'


def _ban_active_text(nickname: str, reason: str, remaining: str) -> str:
    import html
    return (
        f"{_E_YELLOW}{_E_UNLOCK} {html.escape(nickname)}, ожидайте разблокировки бана!\n"
        f"{_E_RED}Вам запрещены любые действия в боте.\n\n"
        f"{_E_MARKER}{_E_MEGA} Причина: {html.escape(reason)}\n"
        f"{_E_MARKER}{_E_RED}{_E_HOUR} Оставшееся время: {html.escape(remaining)} {_E_CLOCK}"
    )


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Determine user_id
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            # Allow certain callbacks through even when banned
            if event.data in _ALLOWED_CALLBACKS:
                return await handler(event, data)

        if user_id and user_id not in ADMIN_IDS:
            if is_player_banned(user_id):
                player = get_player(user_id)
                ban = get_player_ban(user_id)
                if player and ban:
                    remaining = format_ban_remaining(user_id)
                    txt = _ban_active_text(player['nickname'], ban['reason'], remaining)
                    if isinstance(event, Message):
                        await event.answer(txt, reply_markup=get_ban_appeal_kb(), parse_mode="HTML")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("Вы заблокированы!", show_alert=True)
                    return  # Don't process further

        return await handler(event, data)

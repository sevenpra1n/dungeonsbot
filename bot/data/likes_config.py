"""Likes system configuration and formatting helpers.

Provides functions for formatting profile-like notifications and
the like counter displayed on the profile screen.
"""

from bot.data.emojis import E_LIKE_HEART, E_LIKE_THUMB


def format_like_notification(from_nickname: str, personal_message: str = "") -> str:
    """Return the notification text sent to a player whose profile was liked.

    Args:
        from_nickname:    The nickname of the player who gave the like.
        personal_message: Optional personal note attached to the like.

    Example::

        format_like_notification("ауч")
        # → "❤️👍 ваш профиль оценил ауч!"

        format_like_notification("ауч", "Отличный профиль!")
        # → "❤️👍 ваш профиль оценил ауч!\n\n💬 ауч: Отличный профиль!"
    """
    text = f"{E_LIKE_HEART}{E_LIKE_THUMB} ваш профиль оценил {from_nickname}!"
    if personal_message:
        text += f"\n\n💬 {from_nickname}: {personal_message}"
    return text


def format_likes_count(count: int) -> str:
    """Return the likes line shown on the profile screen.

    Example::

        format_likes_count(5)
        # → "❤️ 5 лайков профиля"
    """
    return f"{E_LIKE_HEART} {count} лайков профиля"

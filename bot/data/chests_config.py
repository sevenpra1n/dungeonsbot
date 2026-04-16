"""Chest display configuration and opening animation helpers.

Provides UI-level data for each chest type and functions to format
chest-opening messages (progress animation and reward summary).
"""

from bot.data.emojis import (
    E_CHEST, E_GEAR, E_REWARD, E_PLUS,
)

# Display info for each chest type (name, emoji, drop label)
CHEST_DISPLAY = {
    "chest_wood": {
        "name":       "Деревянный сундук",
        "emoji":      E_CHEST,
        "drop_label": "низкий",
    },
    "chest_steel": {
        "name":       "Стальной сундук",
        "emoji":      E_CHEST,
        "drop_label": "средний",
    },
    "chest_gold": {
        "name":       "Золотой сундук",
        "emoji":      E_CHEST,
        "drop_label": "высокий",
    },
    "chest_divine": {
        "name":       "Всевышний сундук",
        "emoji":      E_CHEST,
        "drop_label": "очень высокий",
    },
}

# Progress steps (%) shown during the opening animation
OPENING_STEPS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]


def format_chest_opening(chest_key: str, progress: int) -> str:
    """Return the opening-animation message for a chest at *progress* percent.

    ``progress`` must be one of the values in OPENING_STEPS (10–100).
    """
    info = CHEST_DISPLAY.get(chest_key, CHEST_DISPLAY["chest_wood"])
    return f"{info['emoji']}{E_GEAR} открываем сундук…\n\n{info['emoji']}{E_GEAR} {progress}%"


def format_chest_reward(chest_key: str, rewards: dict) -> str:
    """Build the reward-summary message after a chest has been opened.

    ``rewards`` is a dict mapping reward labels (e.g. "Монеты") to values.
    Example::

        format_chest_reward("chest_wood", {"Монеты": 55, "Древесина": 3})
    """
    info = CHEST_DISPLAY.get(chest_key, CHEST_DISPLAY["chest_wood"])
    lines = [f"{E_REWARD} Вы открыли {info['name']}:\n"]
    for label, value in rewards.items():
        lines.append(f"{E_PLUS} {label}: {value}")
    return "\n".join(lines)

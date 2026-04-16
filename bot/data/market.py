"""Market configuration constants."""

from bot.emojis import E_FOOD, E_WOOD, E_STONE, E_IRON, E_GOLD_M

# ============== MARKET CONFIG ==============
MARKET_PRICES = {
    'food':  0.7,
    'wood':  2.0,
    'stone': 8.0,
    'iron':  40.0,
    'gold':  160.0,
}
MARKET_RAID_TICKET_PRICE = 57  # монет за 1 билет рейда

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

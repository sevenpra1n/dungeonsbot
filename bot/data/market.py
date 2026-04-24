"""Market configuration constants."""

from bot.data.emojis import (
    E_MAT_FOOD, E_MAT_WOOD, E_MAT_STONE,
    E_MAT_IRON, E_MAT_GOLD, E_MAT_STEEL, E_MAT_AMETHYST, E_MAT_GEM,
)

# ============== MARKET CONFIG ==============
MARKET_PRICES = {
    'food':     0.7,
    'wood':     2.0,
    'stone':    8.0,
    'iron':     40.0,
    'gold':     160.0,
    'steel':    800.0,
    'amethyst': 1650.0,
    'gem':      8700.0,
}
MARKET_RAID_TICKET_PRICE = 57  # монет за 1 билет рейда

# Material key -> (display emoji, accusative name, action label)
_MARKET_MAT_INFO = {
    'food':     (E_MAT_FOOD,     'Еду',        "Продать"),
    'wood':     (E_MAT_WOOD,     'Древесину',  "Продать"),
    'stone':    (E_MAT_STONE,    'Камень',     "Продать"),
    'iron':     (E_MAT_IRON,     'Железо',     "Продать"),
    'gold':     (E_MAT_GOLD,     'Золото',     "Продать"),
    'steel':    (E_MAT_STEEL,    'Сталь',      "Продать"),
    'amethyst': (E_MAT_AMETHYST, 'Аметист',    "Продать"),
    'gem':      (E_MAT_GEM,      'Самоцвет',   "Продать"),
}

# Button text -> material key (plain emoji for keyboard buttons, no HTML tags)
_MARKET_SELL_BUTTONS = {
    "Продать еду🥕":         'food',
    "Продать древесину🌳":   'wood',
    "Продать камень🪨":      'stone',
    "Продать железо⛰":      'iron',
    "Продать золото🥇":      'gold',
    "Продать сталь🌋":       'steel',
    "Продать аметист🤩":     'amethyst',
    "Продать самоцвет🎁":    'gem',
}

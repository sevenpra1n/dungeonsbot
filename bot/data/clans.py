"""Clan configuration constants."""

# ============== CLAN LEVEL CONFIG ==============
CLAN_LEVEL_EXP = {
    1:  100,
    2:  400,
    3:  900,
    4:  1450,
    5:  3000,
    6:  4250,
    7:  6200,
    8:  9500,
    9:  11500,
    10: 14000,
    11: 18500,
    12: 24000,
    13: 55000,
    14: 85000,
}
MAX_CLAN_LEVEL = 15

# ============== CLAN LEAGUES ==============
# (level, name, emoji_id, fallback_char)
CLAN_LEAGUES = {
    1:  ("Новичковая лига",         "5935861406862677914", "🎁"),
    2:  ("Лига Рекрутов",           "5872699720886916484", "🎁"),
    3:  ("Лига Скитальцев",         "5393122856571788805", "😺"),
    4:  ("Кирпичная лига",          "6005979836051363343", "🧱"),
    5:  ("Серебряная лига",         "5837149417584467172", "🏆"),
    6:  ("Лига Охотников",          "5796297917752941521", "👹"),
    7:  ("Золотая лига",            "6017157771907045891", "🖖"),
    8:  ("Лига Хранителей",         "5998973374297022205", "🎁"),
    9:  ("Платиновая лига",         "5999329470035532435", "🦅"),
    10: ("Алмазная лига",           "6278331700929892142", "💎"),
    11: ("Лига Древних Героев",     "6280757262235471883", "🌋"),
    12: ("Лига Бессмертных",        "5895286915241875844", "🎁"),
    13: ("Лига Астральных Богов",   "5886484710481205789", "🎁"),
    14: ("Легендарная лига",        "6021486768228940485", "🎁"),
    15: ("Лучшая лига",             "5936138290519349485", "🎁"),
}


def get_clan_league(level: int) -> tuple[str, str]:
    """Вернуть (tg-emoji строку, название лиги) по уровню клана."""
    lvl = max(1, min(level, MAX_CLAN_LEVEL))
    name, emoji_id, fallback = CLAN_LEAGUES[lvl]
    emoji_str = f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'
    return emoji_str, name


# ============== CLAN BUFFS ==============
CLAN_BUFFS = {
    1:  {"power_pct": 0.0,   "click_bonus": 0},
    2:  {"power_pct": 0.05,  "click_bonus": 5},
    3:  {"power_pct": 0.10,  "click_bonus": 30},
    4:  {"power_pct": 0.30,  "click_bonus": 100},
    5:  {"power_pct": 0.60,  "click_bonus": 250},
    6:  {"power_pct": 0.70,  "click_bonus": 350},
    7:  {"power_pct": 0.80,  "click_bonus": 450},
    8:  {"power_pct": 0.90,  "click_bonus": 600},
    9:  {"power_pct": 1.00,  "click_bonus": 750},
    10: {"power_pct": 1.10,  "click_bonus": 900},
    11: {"power_pct": 1.20,  "click_bonus": 1100},
    12: {"power_pct": 1.35,  "click_bonus": 1350},
    13: {"power_pct": 1.50,  "click_bonus": 1600},
    14: {"power_pct": 1.70,  "click_bonus": 2000},
    15: {"power_pct": 2.00,  "click_bonus": 2500},
}

CLAN_CHAT_MAX_MSG_LEN = 200  # Максимальная длина сообщения в чате клана

# ============== CLAN BOSS CONFIG ==============
BOSS_HEALTH_MULTIPLIER = 0.9   # Здоровье босса = сила * BOSS_HEALTH_MULTIPLIER
MAX_CLAN_BOSS_TICKETS = 3       # Максимум билетов кланового босса на игрока
TICKET_REFRESH_INTERVAL_SECONDS = 3600  # Интервал обновления билетов (1 час)

CLAN_BOSSES_CONFIG = {
    1: {
        "name": "Подземельный мастер",
        "strength": 75000,
        "health": int(75000 * BOSS_HEALTH_MULTIPLIER),   # 67500
        "damage": 175,
        "rewards": {
            "crystals_base": 10,
            "crystals_bonus": 5,
            "crystals_bonus_chance": 0.20,
            "coins_by_strength": [(200, 1200), (800, 2500), (None, 8500)],
            "exp_profile": (220, 300),
            "exp_clan": 120,
            "rating": 50,
        },
        "cooldown_minutes": 30,
    },
    2: {
        "name": "Заклятый дух клана",
        "strength": 290000,
        "health": int(290000 * BOSS_HEALTH_MULTIPLIER),  # 261000
        "damage": 460,
        "rewards": {
            "crystals_base": 50,
            "crystals_bonus": 100,
            "crystals_bonus_chance": 0.20,
            "coins_by_strength": [(200, 5600), (800, 8900), (None, 15000)],
            "exp_profile": (1250, 1250),
            "exp_clan": 450,
            "rating": 100,
        },
        "cooldown_minutes": 30,
    },
}

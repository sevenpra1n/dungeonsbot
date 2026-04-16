"""Clan configuration constants."""

# ============== CLAN LEVEL CONFIG ==============
CLAN_LEVEL_EXP = {1: 100, 2: 250, 3: 500, 4: 950, 5: 1500}
MAX_CLAN_LEVEL = 5

# ============== CLAN BUFFS ==============
CLAN_BUFFS = {
    1: {"power_pct": 0.0,  "click_bonus": 0},
    2: {"power_pct": 0.05, "click_bonus": 5},
    3: {"power_pct": 0.10, "click_bonus": 30},
    4: {"power_pct": 0.30, "click_bonus": 100},
    5: {"power_pct": 0.60, "click_bonus": 250},
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

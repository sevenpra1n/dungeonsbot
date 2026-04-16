"""Location, location enemies, forest enemies, and axes data."""

from bot.emojis import E_FOOD, E_MAP_E

# ============== LOCATIONS ==============
LOCATIONS = {
    1: {
        "name": "🌾 Ясная Поляна",
        "emoji": "🌾",
        "image": "images/meadow.png",
        "activities": {
            "gather": {
                "name": "Добыча еды",
                "time": 25,
                "emoji": "🥕",
                "display_emoji": E_FOOD,
                "rewards": {
                    "food": (2, 5),
                    "experience": (3, 8),
                    "coins": (10, 25)
                },
                "monster_chance": 0
            },
            "search": {
                "name": "Обыскать локацию",
                "time": 50,
                "emoji": "🗺️",
                "display_emoji": E_MAP_E,
                "rewards": {
                    "coins": (20, 50),
                    "experience": (5, 15),
                    "food": (1, 3)
                },
                "monster_chance": 0.05
            }
        }
    },
    2: {
        "name": "🌳 Лес",
        "emoji": "🌳",
        "image": "images/les.png",
        "activities": {
            "chop_wood": {
                "name": "Добыча древесины",
                "time": 40,
                "emoji": "🌳",
                "display_emoji": "🌳",
                "rewards": {},
                "monster_chance": 0
            },
            "search": {
                "name": "Обыскать локацию",
                "time": 60,
                "emoji": "🗺️",
                "display_emoji": E_MAP_E,
                "rewards": {
                    "coins": (10, 30),
                    "experience": (9, 9),
                },
                "monster_chance": 0
            }
        }
    }
}

# Враги в локациях: порог определяется силой игрока
LOCATION_ENEMIES = {
    "goblin": {
        "name": "Гоблин",
        "emoji": "👺",
        "strength": 35,
        "min_player_strength": 0,
        "max_player_strength": 99,
        "rewards": {
            "coins": (10, 30),
            "rating_points": 2,
            "clan_exp": (2, 5),
            "experience": (3, 9),
            "food": (2, 2),
            "food_chance": 0.20,
        },
    },
    "angry_hawk": {
        "name": "Яростный ястреб",
        "emoji": "🦅",
        "strength": 125,
        "min_player_strength": 100,
        "max_player_strength": 9999,
        "rewards": {
            "coins": (50, 60),
            "food": (3, 9),
            "clan_exp": (8, 15),
            "experience": (10, 16),
            "crystals": 1,
            "crystals_chance": 0.05,
        },
    },
}

# Топоры (для магазина предметов)
AXES = {
    1: {"level": 1, "min_wood": 2,  "max_wood": 6,   "cost": 250,   "star_emoji": '<tg-emoji emoji-id="5204460680018666213">⭐️</tg-emoji>'},
    2: {"level": 2, "min_wood": 8,  "max_wood": 14,  "cost": 900,   "star_emoji": '<tg-emoji emoji-id="5204221415980539813">⭐️</tg-emoji>'},
    3: {"level": 3, "min_wood": 17, "max_wood": 35,  "cost": 3250,  "star_emoji": '<tg-emoji emoji-id="5204347567759956677">⭐️</tg-emoji>'},
    4: {"level": 4, "min_wood": 30, "max_wood": 75,  "cost": 9500,  "star_emoji": '<tg-emoji emoji-id="5204141284775697953">⭐️</tg-emoji>'},
    5: {"level": 5, "min_wood": 80, "max_wood": 115, "cost": 25300, "star_emoji": '<tg-emoji emoji-id="5217979901331644711">⭐️</tg-emoji>'},
}

# Враги леса (по силе игрока)
FOREST_ENEMIES = {
    "lizard": {
        "name": "Ящерица",
        "emoji": "🦎",
        "strength": 80,
        "min_player_strength": 0,
        "max_player_strength": 89,
        "rewards": {
            "coins": (10, 30),
            "experience": (5, 12),
            "clan_exp": (6, 10),
        },
    },
    "forest_archer": {
        "name": "Лесной лучник",
        "emoji": "🏹",
        "strength": 135,
        "min_player_strength": 90,
        "max_player_strength": 199,
        "rewards": {
            "coins": (35, 90),
            "wood": (4, 10),
            "experience": (15, 20),
            "clan_exp": (10, 15),
        },
    },
    "forest_brute": {
        "name": "Лесной громила",
        "emoji": "👹",
        "strength": 475,
        "min_player_strength": 200,
        "max_player_strength": 999999,
        "rewards": {
            "coins": (120, 250),
            "wood": (4, 10),
            "experience": (15, 20),
            "clan_exp": (10, 15),
        },
    },
}


def get_location_enemy_for_player(player_strength: float) -> dict:
    """Вернуть врага локации по силе игрока"""
    for enemy in LOCATION_ENEMIES.values():
        if enemy['min_player_strength'] <= player_strength <= enemy['max_player_strength']:
            return enemy
    # fallback
    return LOCATION_ENEMIES["goblin"]


def get_forest_enemy_for_player(player_strength: float) -> dict:
    """Вернуть врага леса по силе игрока"""
    for enemy in FOREST_ENEMIES.values():
        if enemy['min_player_strength'] <= player_strength <= enemy['max_player_strength']:
            return enemy
    # fallback to strongest
    return FOREST_ENEMIES["forest_brute"]

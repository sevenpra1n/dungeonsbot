"""Location, location enemies, forest enemies, axes and pickaxes data."""

from bot.emojis import E_FOOD, E_MAP_E, E_IRON, E_SKULL
from bot.data.emojis import E_MAT_STONE
from bot.data.emojis import (
    E_MAP_HEADER, E_GREEN_MARKER, E_MARKER, E_YELLOW_MARKER, E_HOURGLASS,
    E_BREAD, E_MOUNTAIN, E_STONE, E_BONES, E_EYE, E_FIRE, E_SEARCH, E_LEVEL,
    E_WARNING, E_FORBIDDEN, E_LOCATION_ICON, E_MAP_ICON, E_KEY, E_SKULL as E_SKULL_MD,
    E_GIFT_REWARD,
)

# Pickaxe custom emoji for the LOCATION MENU (mine ore activity row)
E_PICKAXE_LOC  = '<tg-emoji emoji-id="5469636217186303242">⛏️</tg-emoji>'

# Pickaxe custom emoji for the ITEMS SHOP listing (HTML format, kept for legacy use)
E_PICKAXE_SHOP = '<tg-emoji emoji-id="5469636217186303242">⛏️</tg-emoji>'

# Stone emoji used in pickaxe shop descriptions (taken from inventory config)
E_STONE_MAT = E_MAT_STONE

# ── MarkdownV2 emoji constants for the pickaxes shop ────────────────────────
_E_MARKER_MD  = '![▫️](tg://emoji?id=5267324424113124134)'
_E_PICKAXE_MD = '![⛏️](tg://emoji?id=5469636217186303242)'
_E_IRON_MD    = '![⛰](tg://emoji?id=6278216436892570592)'
_E_COINS_MD   = '![👛](tg://emoji?id=5215420556089776398)'
_E_COMP_MD    = '![⚙️](tg://emoji?id=5398095118735521227)'

_PICKAXE_STAR_MD = {
    1: '![⭐️](tg://emoji?id=5204460680018666213)',
    2: '![⭐️](tg://emoji?id=5204221415980539813)',
    3: '![⭐️](tg://emoji?id=5204347567759956677)',
    4: '![⭐️](tg://emoji?id=5204141284775697953)',
    5: '![⭐️](tg://emoji?id=5217979901331644711)',
}

_PICKAXE_RARITY_MD = {
    "common":    '![🌟](tg://emoji?id=5395855331945392566)',
    "rare":      '![🌟](tg://emoji?id=5395316601312548706)',
    "epic":      '![🌟](tg://emoji?id=5395550054259921224)',
    "legendary": '![🌟](tg://emoji?id=5395487888903280719)',
}

# ============== LOCATIONS ==============
LOCATIONS = {
    1: {
        "name": "🌾 Ясная поляна",
        "emoji": "🌾",
        "image": "images/meadow.png",
        "min_level": 1,
        "enemy_search_time": 10,
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
                "monster_chance": 0.10
            }
        }
    },
    2: {
        "name": "🌳 Лес",
        "emoji": "🌳",
        "image": "images/les.png",
        "min_level": 1,
        "enemy_search_time": 30,
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
                "monster_chance": 0.18
            }
        }
    },
    3: {
        "name": "⛏ Шахта",
        "emoji": "⛏",
        "image": "images/mine.png",
        "min_level": 3,
        "enemy_search_time": 60,
        "activities": {
            "mine_ore": {
                "name": "Добыча руды",
                "time": 60,
                "emoji": "⛏",
                "display_emoji": E_PICKAXE_LOC,
                "rewards": {},
                "monster_chance": 0
            },
            "search": {
                "name": "Обыскать локацию",
                "time": 90,
                "emoji": "🗺️",
                "display_emoji": E_MAP_E,
                "rewards": {},
                "monster_chance": 0.25
            }
        }
    },
    4: {
        "name": "🦂 Дикие пустоши",
        "emoji": "🦂",
        "image": "images/pustosh.png",
        "min_level": 10,
        "enemy_search_time": 120,
        "activities": {
            "search": {
                "name": "Обыскать локацию",
                "time": 150,
                "emoji": "🗺️",
                "display_emoji": E_MAP_E,
                "rewards": {},
                "monster_chance": 0.35
            },
            "loot_all": {
                "name": "Обчистить всю локацию",
                "time": 600,
                "emoji": "🧹",
                "display_emoji": "🧹",
                "rewards": {},
                "monster_chance": 1.0
            }
        }
    },
    5: {
        "name": "🏜 Далёкие земли",
        "emoji": "🏜",
        "image": "images/dalekie.png",
        "min_level": 18,
        "enemy_search_time": 210,
        "activities": {
            "search": {
                "name": "Обыскать локацию",
                "time": 240,
                "emoji": "🗺️",
                "display_emoji": E_MAP_E,
                "rewards": {},
                "monster_chance": 0.5
            },
            "loot_all": {
                "name": "Обчистить всю локацию",
                "time": 1200,
                "emoji": "🧹",
                "display_emoji": "🧹",
                "rewards": {},
                "monster_chance": 1.0
            }
        }
    },
    6: {
        "name": "🔥 Преисподня",
        "emoji": "🔥",
        "image": "images/preispodnya.png",
        "min_level": 25,
        "enemy_search_time": 600,
        "activities": {
            "search": {
                "name": "Обыскать локацию",
                "time": 600,
                "emoji": "🗺️",
                "display_emoji": E_MAP_E,
                "rewards": {},
                "monster_chance": 0.65
            },
            "loot_all": {
                "name": "Обчистить всю локацию",
                "time": 2100,
                "emoji": "🧹",
                "display_emoji": "🧹",
                "rewards": {},
                "monster_chance": 1.0
            }
        }
    },
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

# Кирки (для магазина предметов)
PICKAXES = {
    1: {
        "name": "Деревянная кирка",
        "level": 1, "min_stone": 1,  "max_stone": 3,   "cost": 850,
        "comp_rarity": "common",    "comp_amount": 4,  "comp_name": "обычных",
        "comp_word": "компонента",
        "star_emoji": '<tg-emoji emoji-id="5204460680018666213">⭐️</tg-emoji>',
        "stone_amount": (3, 6),
        "ore_chances": {
            "copper": 0.10, "iron": 0.05, "gold": 0.01,
            "steel": 0.0,  "amethyst": 0.0, "gem": 0.0,
        },
        "ore_amounts": {
            "copper": (1, 5), "iron": (1, 3), "gold": (1, 1),
            "steel": (1, 1),  "amethyst": (1, 1), "gem": (1, 1),
        },
        "experience": (4, 10),
    },
    2: {
        "name": "Каменная кирка",
        "level": 2, "min_stone": 2,  "max_stone": 9,   "cost": 1570,
        "comp_rarity": "common",    "comp_amount": 35, "comp_name": "обычных",
        "comp_word": "компонента",
        "star_emoji": '<tg-emoji emoji-id="5204221415980539813">⭐️</tg-emoji>',
        "stone_amount": (6, 14),
        "ore_chances": {
            "copper": 0.20, "iron": 0.10, "gold": 0.03,
            "steel": 0.001, "amethyst": 0.0, "gem": 0.0,
        },
        "ore_amounts": {
            "copper": (2, 10), "iron": (1, 6), "gold": (1, 3),
            "steel": (1, 1),   "amethyst": (1, 1), "gem": (1, 1),
        },
        "experience": (8, 20),
    },
    3: {
        "name": "Железная кирка",
        "level": 3, "min_stone": 5,  "max_stone": 18,  "cost": 6250,
        "comp_rarity": "rare",      "comp_amount": 10, "comp_name": "редких",
        "comp_word": "компонента",
        "star_emoji": '<tg-emoji emoji-id="5204347567759956677">⭐️</tg-emoji>',
        "stone_amount": (10, 32),
        "ore_chances": {
            "copper": 0.50, "iron": 0.25, "gold": 0.08,
            "steel": 0.01,  "amethyst": 0.001, "gem": 0.0,
        },
        "ore_amounts": {
            "copper": (5, 18), "iron": (4, 12), "gold": (2, 6),
            "steel": (1, 4),   "amethyst": (1, 2), "gem": (1, 1),
        },
        "experience": (12, 40),
    },
    4: {
        "name": "Алмазная кирка",
        "level": 4, "min_stone": 10, "max_stone": 37,  "cost": 12500,
        "comp_rarity": "epic",      "comp_amount": 24, "comp_name": "эпических",
        "comp_word": "компонентов",
        "star_emoji": '<tg-emoji emoji-id="5204141284775697953">⭐️</tg-emoji>',
        "stone_amount": (24, 75),
        "ore_chances": {
            "copper": 0.80, "iron": 0.40, "gold": 0.14,
            "steel": 0.08,  "amethyst": 0.01, "gem": 0.0,
        },
        "ore_amounts": {
            "copper": (18, 34), "iron": (12, 24), "gold": (4, 12),
            "steel": (2, 8),    "amethyst": (2, 6), "gem": (1, 1),
        },
        "experience": (24, 80),
    },
    5: {
        "name": "Незеритовая кирка",
        "level": 5, "min_stone": 25, "max_stone": 115, "cost": 56300,
        "comp_rarity": "legendary", "comp_amount": 12, "comp_name": "легендарных",
        "comp_word": "компонентов",
        "star_emoji": '<tg-emoji emoji-id="5217979901331644711">⭐️</tg-emoji>',
        "stone_amount": (45, 135),
        "ore_chances": {
            "copper": 1.0,  "iron": 1.0,  "gold": 0.45,
            "steel": 0.20,  "amethyst": 0.095, "gem": 0.03,
        },
        "ore_amounts": {
            "copper": (22, 55), "iron": (18, 45), "gold": (6, 24),
            "steel": (4, 12),   "amethyst": (3, 10), "gem": (1, 4),
        },
        "experience": (60, 140),
    },
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

# Враги шахты (по силе игрока) — сильнее врагов леса
MINE_ENEMIES = {
    "mine_rat": {
        "name": "Шахтная крыса",
        "emoji": "🐀",
        "strength": 110,
        "min_player_strength": 0,
        "max_player_strength": 149,
        "rewards": {
            "coins": (20, 50),
            "iron": (1, 3),
            "experience": (8, 15),
            "clan_exp": (8, 12),
        },
    },
    "cave_troll": {
        "name": "Пещерный тролль",
        "emoji": "👾",
        "strength": 240,
        "min_player_strength": 150,
        "max_player_strength": 399,
        "rewards": {
            "coins": (55, 120),
            "iron": (2, 7),
            "experience": (18, 28),
            "clan_exp": (12, 18),
        },
    },
    "stone_golem": {
        "name": "Каменный голем",
        "emoji": "🪨",
        "strength": 650,
        "min_player_strength": 400,
        "max_player_strength": 899,
        "rewards": {
            "coins": (150, 300),
            "iron": (5, 15),
            "experience": (25, 40),
            "clan_exp": (15, 22),
        },
    },
    "iron_giant": {
        "name": "Железный великан",
        "emoji": "🤖",
        "strength": 1500,
        "min_player_strength": 900,
        "max_player_strength": 999999,
        "rewards": {
            "coins": (300, 600),
            "iron": (10, 30),
            "experience": (40, 65),
            "clan_exp": (20, 30),
        },
    },
}

# Враги диких пустошей (по силе игрока)
WASTELAND_ENEMIES = {
    "dust_scavenger": {
        "name": "Пылевой мародёр",
        "emoji": "🪓",
        "strength": 95,
        "min_player_strength": 0,
        "max_player_strength": 99,
        "rewards": {
            "coins": (20, 60),
            "experience": (10, 18),
            "clan_exp": (6, 12),
        },
    },
    "rabid_hyena": {
        "name": "Бешеная гиена",
        "emoji": "🐺",
        "strength": 185,
        "min_player_strength": 100,
        "max_player_strength": 399,
        "rewards": {
            "coins": (45, 110),
            "experience": (18, 30),
            "clan_exp": (10, 16),
            "iron": (1, 2),
        },
    },
    "ash_stalker": {
        "name": "Пепельный охотник",
        "emoji": "🦂",
        "strength": 520,
        "min_player_strength": 400,
        "max_player_strength": 899,
        "rewards": {
            "coins": (130, 240),
            "experience": (32, 50),
            "clan_exp": (14, 22),
            "iron": (2, 5),
            "gold": (1, 2),
        },
    },
    "waste_reaver": {
        "name": "Разоритель пустошей",
        "emoji": "☠️",
        "strength": 1150,
        "min_player_strength": 900,
        "max_player_strength": 1699,
        "rewards": {
            "coins": (260, 420),
            "experience": (50, 75),
            "clan_exp": (20, 28),
            "iron": (4, 9),
            "gold": (1, 3),
            "steel": (1, 1),
        },
    },
    "sand_titan": {
        "name": "Песчаный титан",
        "emoji": "🗿",
        "strength": 1900,
        "min_player_strength": 1700,
        "max_player_strength": 999999,
        "rewards": {
            "coins": (420, 700),
            "experience": (75, 110),
            "clan_exp": (26, 38),
            "iron": (6, 14),
            "gold": (2, 5),
            "steel": (1, 2),
        },
    },
}

# Враги дальних земель (по силе игрока)
FARLANDS_ENEMIES = {
    "nomad_saboteur": {
        "name": "Кочевой диверсант",
        "emoji": "🗡️",
        "strength": 210,
        "min_player_strength": 0,
        "max_player_strength": 149,
        "rewards": {
            "coins": (40, 100),
            "experience": (18, 28),
            "clan_exp": (8, 14),
            "iron": (1, 3),
        },
    },
    "storm_raider": {
        "name": "Штормовой налётчик",
        "emoji": "🌪",
        "strength": 540,
        "min_player_strength": 150,
        "max_player_strength": 499,
        "rewards": {
            "coins": (110, 220),
            "experience": (30, 48),
            "clan_exp": (14, 20),
            "iron": (2, 6),
            "gold": (1, 2),
        },
    },
    "rift_hunter": {
        "name": "Охотник разлома",
        "emoji": "🕳",
        "strength": 980,
        "min_player_strength": 500,
        "max_player_strength": 1099,
        "rewards": {
            "coins": (220, 420),
            "experience": (48, 72),
            "clan_exp": (20, 28),
            "iron": (4, 10),
            "gold": (2, 4),
            "steel": (1, 1),
        },
    },
    "obsidian_keeper": {
        "name": "Обсидиановый страж",
        "emoji": "🛡️",
        "strength": 1680,
        "min_player_strength": 1100,
        "max_player_strength": 1999,
        "rewards": {
            "coins": (420, 700),
            "experience": (72, 105),
            "clan_exp": (26, 36),
            "iron": (7, 16),
            "gold": (2, 6),
            "steel": (1, 2),
        },
    },
    "ancient_warden": {
        "name": "Древний надзиратель",
        "emoji": "👹",
        "strength": 2450,
        "min_player_strength": 2000,
        "max_player_strength": 999999,
        "rewards": {
            "coins": (720, 1150),
            "experience": (110, 160),
            "clan_exp": (34, 48),
            "iron": (10, 22),
            "gold": (4, 8),
            "steel": (1, 3),
        },
    },
}

# Враги преисподни (по силе игрока)
HELL_ENEMIES = {
    "ember_hound": {
        "name": "Угольная гончая",
        "emoji": "🔥",
        "strength": 380,
        "min_player_strength": 0,
        "max_player_strength": 249,
        "rewards": {
            "coins": (70, 160),
            "experience": (25, 40),
            "clan_exp": (10, 16),
            "iron": (2, 5),
            "gold": (1, 2),
        },
    },
    "soul_reaper": {
        "name": "Жнец душ",
        "emoji": "💀",
        "strength": 920,
        "min_player_strength": 250,
        "max_player_strength": 799,
        "rewards": {
            "coins": (190, 360),
            "experience": (45, 70),
            "clan_exp": (18, 26),
            "iron": (5, 11),
            "gold": (2, 4),
            "steel": (1, 1),
        },
    },
    "infernal_knight": {
        "name": "Инфернальный рыцарь",
        "emoji": "🛡",
        "strength": 1800,
        "min_player_strength": 800,
        "max_player_strength": 1699,
        "rewards": {
            "coins": (360, 620),
            "experience": (72, 105),
            "clan_exp": (26, 36),
            "iron": (8, 18),
            "gold": (3, 7),
            "steel": (1, 2),
        },
    },
    "pit_overseer": {
        "name": "Надзиратель ямы",
        "emoji": "👿",
        "strength": 2900,
        "min_player_strength": 1700,
        "max_player_strength": 2899,
        "rewards": {
            "coins": (650, 1050),
            "experience": (110, 160),
            "clan_exp": (34, 46),
            "iron": (12, 26),
            "gold": (5, 10),
            "steel": (2, 4),
        },
    },
    "lord_of_ashes": {
        "name": "Повелитель пепла",
        "emoji": "👑",
        "strength": 4200,
        "min_player_strength": 2900,
        "max_player_strength": 999999,
        "rewards": {
            "coins": (1100, 1800),
            "experience": (170, 240),
            "clan_exp": (44, 60),
            "iron": (16, 34),
            "gold": (7, 14),
            "steel": (3, 5),
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


def get_mine_enemy_for_player(player_strength: float) -> dict:
    """Вернуть врага шахты по силе игрока"""
    for enemy in MINE_ENEMIES.values():
        if enemy['min_player_strength'] <= player_strength <= enemy['max_player_strength']:
            return enemy
    # fallback to strongest
    return MINE_ENEMIES["iron_giant"]


def get_wasteland_enemy_for_player(player_strength: float) -> dict:
    """Вернуть врага диких пустошей по силе игрока"""
    for enemy in WASTELAND_ENEMIES.values():
        if enemy['min_player_strength'] <= player_strength <= enemy['max_player_strength']:
            return enemy
    return WASTELAND_ENEMIES["sand_titan"]


def get_farlands_enemy_for_player(player_strength: float) -> dict:
    """Вернуть врага дальних земель по силе игрока"""
    for enemy in FARLANDS_ENEMIES.values():
        if enemy['min_player_strength'] <= player_strength <= enemy['max_player_strength']:
            return enemy
    return FARLANDS_ENEMIES["ancient_warden"]


def get_hell_enemy_for_player(player_strength: float) -> dict:
    """Вернуть врага преисподни по силе игрока"""
    for enemy in HELL_ENEMIES.values():
        if enemy['min_player_strength'] <= player_strength <= enemy['max_player_strength']:
            return enemy
    return HELL_ENEMIES["lord_of_ashes"]


def _format_cost_md(cost: int) -> str:
    """Форматировать стоимость с точкой как разделителем тысяч (MarkdownV2-safe)."""
    s = str(cost)
    length = len(s)
    if length <= 3:
        return s
    # Insert escaped dots as thousands separators from the right
    groups = []
    while s:
        groups.append(s[-3:])
        s = s[:-3]
    return '\\.'.join(reversed(groups))


def format_axes_shop_text(current_pickaxe_level: int = 0) -> str:
    """Сформировать текст магазина кирок в формате MarkdownV2."""
    lines = []
    for pick_id, data in PICKAXES.items():
        owned = "✅" if current_pickaxe_level >= pick_id else "❌"
        star_md = _PICKAXE_STAR_MD[pick_id]
        rarity_md = _PICKAXE_RARITY_MD.get(data['comp_rarity'], '')
        cost_md = _format_cost_md(data['cost'])
        comp_amount = data['comp_amount']
        comp_name = data['comp_name']
        comp_word = data.get('comp_word', 'компонента')
        pickaxe_name = data.get('name', f'Кирка {pick_id}')
        lines.append(
            f"{_E_MARKER_MD}{pickaxe_name} \\- {_E_PICKAXE_MD} {pick_id} level {star_md}\n"
            f"├ в наличии {owned}\n"
            f"![🔘](tg://emoji?id=5357471466919056181)Цена \\- {cost_md}{_E_COINS_MD}\n"
            f"![🔘](tg://emoji?id=5357471466919056181)Нужно \\- {comp_amount} {_E_COMP_MD}{rarity_md}\n"
        )
    return "\n".join(lines)


def format_map_text(user_id: int, current_activity: dict = None) -> str:
    """Вывести меню карты с правильными эмодзи."""
    lines = [f'{E_MAP_HEADER} КАРТА\n']

    if current_activity:
        lines.append(f'{E_GREEN_MARKER} Идёт активность:')
        lines.append(f'{E_MARKER}{E_YELLOW_MARKER}{current_activity["name"]}')
        lines.append(f'{E_MARKER}Осталось: {E_HOURGLASS}{current_activity["remaining_seconds"]} секунд...\n')

    lines.append('Выбери локацию для исследования:\n')

    lines.append(f'{E_YELLOW_MARKER}{E_BREAD} Ясная поляна:')
    lines.append(f'{E_MARKER}Здесь можно добыть еду\n')

    lines.append(f'{E_YELLOW_MARKER}{E_MOUNTAIN} Лес:')
    lines.append(f'{E_MARKER}Здесь можно добыть древесину\n')

    lines.append(f'{E_YELLOW_MARKER}{E_STONE} Шахта:')
    lines.append(f'{E_MARKER}Здесь можно добыть кучу ресурсов\\!')
    lines.append(f'{E_SEARCH} Минимальный порог входа: 3 {E_LEVEL} уровень опыта\n')

    lines.append(f'{E_YELLOW_MARKER}{E_BONES} Дикие пустоши:')
    lines.append(f'{E_MARKER}Опасная локация, только для опытных')
    lines.append(f'{E_SEARCH} Минимальный порог входа: 10 {E_LEVEL} уровень опыта\n')

    lines.append(f'{E_YELLOW_MARKER}{E_EYE} Далёкие земли:')
    lines.append(f'{E_MARKER}Здесь очень ценные ресурсы, но высокий шанс умереть\\.\\.')
    lines.append(f'{E_SEARCH} Минимальный порог входа: 18 {E_LEVEL} уровень опыта\n')

    lines.append(f'{E_YELLOW_MARKER}{E_FIRE} Преисподня:')
    lines.append(f'{E_MARKER}Последняя локация, для тех кто хочет пройти игру\\.')
    lines.append(f'{E_SEARCH} Минимальный порог входа: 25 {E_LEVEL} уровень опыта')

    return '\n'.join(lines)


def format_location_wildlands_text() -> str:
    """Меню локации Дикие пустоши."""
    return (
        f'{E_BONES} Дикие пустоши:\n\n'
        f'{E_LOCATION_ICON} Выбери действие:\n\n'
        f'2\\.3m{E_HOURGLASS} │ {E_MAP_ICON} │ Обыскать локацию\n\n'
        f'10m{E_HOURGLASS} │ {E_KEY} │ Обчистить всю локацию\n'
        f'{E_MARKER}{E_WARNING} Внимание: 100% шанс на врага\n\n'
        f'2m{E_HOURGLASS} │ {E_SKULL_MD} │ Поиск врага'
    )


def format_location_distant_text() -> str:
    """Меню локации Далёкие земли."""
    return (
        f'{E_EYE} Далёкие земли:\n\n'
        f'{E_LOCATION_ICON} Выбери действие:\n\n'
        f'4m{E_HOURGLASS} │ {E_MAP_ICON} │ Обыскать локацию\n\n'
        f'20m{E_HOURGLASS} │ {E_KEY} │ Обчистить всю локацию\n'
        f'{E_MARKER}{E_WARNING} Внимание: 100% шанс на врага\n\n'
        f'3\\.5m{E_HOURGLASS} │ {E_SKULL_MD} │ Поиск врага'
    )


def format_location_hell_text() -> str:
    """Меню локации Преисподня."""
    return (
        f'{E_FIRE} Преисподня:\n\n'
        f'{E_LOCATION_ICON} Выбери действие:\n\n'
        f'10m{E_HOURGLASS} │ {E_GIFT_REWARD} │ Обыскать локацию\n\n'
        f'35m{E_HOURGLASS} │ {E_KEY} │ Обчистить всю локацию\n'
        f'{E_MARKER}{E_WARNING} Внимание: 100% шанс на врага\n\n'
        f'10m{E_HOURGLASS} │ {E_SKULL_MD} │ Поиск врага'
    )


def format_account_delete_warning() -> str:
    """Предупреждение об удалении аккаунта."""
    return (
        f'{E_WARNING}{E_FORBIDDEN} Вы точно хотите сбросить данные аккаунта?\n'
        f'{E_MARKER}Весь прогресс потеряется и вы начнете заново\\!\n\n'
        f'{E_YELLOW_MARKER} Ниже напишите "ПОДТВЕРДИТЬ" чтобы удалить аккаунт\\.'
    )

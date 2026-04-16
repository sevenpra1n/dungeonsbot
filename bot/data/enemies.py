"""Enemy, raid floor, and battle data constants."""

# ============== ENEMIES ==============
ENEMIES = {
    1: {"name": "Гоблин", "health": 50, "reward": 30, "base_damage": 8, "rating_points": 5},
    2: {"name": "Лучник", "health": 120, "reward": 60, "base_damage": 15, "rating_points": 10},
    3: {"name": "Дровосек", "health": 300, "reward": 90, "base_damage": 25, "rating_points": 15},
    4: {"name": "Гоблин-гигант", "health": 640, "reward": 120, "base_damage": 40, "rating_points": 25},
    5: {"name": "Дух леса", "health": 950, "reward": 190, "base_damage": 60, "rating_points": 40}
}

# ============== RAID FLOORS ==============
RAID_FLOORS = {
    1:  {"name": "летучая мышь",      "health": 60,   "reward": 10,  "base_damage": 15,  "emoji": "💀"},
    2:  {"name": "крыса",             "health": 140,  "reward": 25,  "base_damage": 35,  "emoji": "💀"},
    3:  {"name": "слизень",           "health": 200,  "reward": 40,  "base_damage": 50,  "emoji": "💀"},
    4:  {"name": "большой слизень",   "health": 340,  "reward": 80,  "base_damage": 85,  "emoji": "💀"},
    5:  {"name": "скелет",            "health": 440,  "reward": 110, "base_damage": 110, "emoji": "💀"},
    6:  {"name": "гоблин",            "health": 600,  "reward": 145, "base_damage": 150, "emoji": "💀"},
    7:  {"name": "проклятый доспех",  "health": 740,  "reward": 210, "base_damage": 185, "emoji": "💀"},
    8:  {"name": "железная дева",     "health": 840,  "reward": 350, "base_damage": 210, "emoji": "💀"},
    9:  {"name": "призрачный палач",  "health": 1280, "reward": 520, "base_damage": 320, "emoji": "💀"},
    10: {"name": "зеркальный дух",    "health": 2000, "reward": 700, "base_damage": 500, "emoji": "♦️💀"},
}

# CO-OP raid multipliers
COOP_ENEMY_HP_MULT = 1.5
COOP_REWARD_MULT = 1.25

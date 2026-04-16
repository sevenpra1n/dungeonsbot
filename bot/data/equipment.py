"""Equipment, weapons, and armor data constants."""

# ============== EQUIPMENT (legacy) ==============
EQUIPMENT = {
    1: {"name": "деревянный меч", "strength": 15, "cost": 50, "emoji": "🗡️"},
    2: {"name": "железный меч", "strength": 30, "cost": 150, "emoji": "🗡️"},
    3: {"name": "золотой меч", "strength": 50, "cost": 350, "emoji": "🗡️"},
    4: {"name": "кожаная одежда", "strength": 60, "cost": 550, "emoji": "👕"},
    5: {"name": "гаечный ключ", "strength": 85, "cost": 850, "emoji": "🔧"}
}

# ============== FORGE: WEAPONS & ARMOR ==============
DEFAULT_WEAPON = {"name": "палка", "strength": 10, "emoji": "🔹", "rarity": "common"}
DEFAULT_ARMOR = {"name": "трусы", "strength": 10, "emoji": "🔹", "rarity": "common"}

WEAPONS = {
    1:  {"name": "Большая палка",              "strength": 16,   "cost": 90,     "emoji": "🔹", "rarity": "common"},
    2:  {"name": "Деревянный меч",             "strength": 22,   "cost": 170,    "emoji": "🔹", "rarity": "common"},
    3:  {"name": "Каменная булава",            "strength": 31,   "cost": 350,    "emoji": "🔹", "rarity": "common"},
    4:  {"name": "Золотой клинок",             "strength": 40,   "cost": 550,    "emoji": "🔸", "rarity": "uncommon"},
    5:  {"name": "Железный меч",               "strength": 55,   "cost": 790,    "emoji": "🔸", "rarity": "uncommon"},
    6:  {"name": "Зачарованный золотой меч",   "strength": 70,   "cost": 1350,   "emoji": "🔸", "rarity": "uncommon"},
    7:  {"name": "Арбалет",                    "strength": 95,   "cost": 1750,   "emoji": "🔸", "rarity": "rare"},
    8:  {"name": "Длинный тисовый лук",        "strength": 125,  "cost": 2800,   "emoji": "🔸", "rarity": "rare"},
    9:  {"name": "Катана",                     "strength": 165,  "cost": 3900,   "emoji": "🔸", "rarity": "rare"},
    10: {"name": "Нунчаки",                    "strength": 200,  "cost": 5000,   "emoji": "♦️", "rarity": "epic"},
    11: {"name": "Чакрам",                     "strength": 265,  "cost": 6700,   "emoji": "♦️", "rarity": "epic"},
    12: {"name": "Нагината",                   "strength": 320,  "cost": 8600,   "emoji": "♦️", "rarity": "epic"},
    13: {"name": "Алмазный клинок",            "strength": 400,  "cost": 12500,  "emoji": "💎", "rarity": "legendary"},
    14: {"name": "Зачарованная глефа",         "strength": 520,  "cost": 16900,  "emoji": "💎", "rarity": "legendary"},
    15: {"name": "Великий трезубец",           "strength": 640,  "cost": 23000,  "emoji": "💎", "rarity": "legendary"},
    16: {"name": "Могучий боевой молот",       "strength": 770,  "cost": 40000,  "emoji": "🌟", "rarity": "mythic"},
    17: {"name": "Обсидиановый клеймор",       "strength": 850,  "cost": 70000,  "emoji": "🌟", "rarity": "mythic"},
    18: {"name": "Мега-кинжалы охотника",      "strength": 985,  "cost": 100000, "emoji": "🌟", "rarity": "mythic"},
    19: {"name": "Рапира божества",            "strength": 1120, "cost": 145000, "emoji": "🎁", "rarity": "ultra"},
    20: {"name": "Сокрушитель земель",         "strength": 1400, "cost": 220000, "emoji": "🎁", "rarity": "ultra"},
}

ARMOR = {
    1:  {"name": "Тряпичные обмотки",          "strength": 15,   "cost": 100,    "emoji": "🔹", "rarity": "common"},
    2:  {"name": "Конопляная рубаха",          "strength": 17,   "cost": 220,    "emoji": "🔹", "rarity": "common"},
    3:  {"name": "Травяные сандалии",          "strength": 31,   "cost": 370,    "emoji": "🔹", "rarity": "common"},
    4:  {"name": "Кожаная куртка",              "strength": 40,   "cost": 500,    "emoji": "🔸", "rarity": "uncommon"},
    5:  {"name": "Капюшон следопыта",          "strength": 55,   "cost": 820,    "emoji": "🔸", "rarity": "uncommon"},
    6:  {"name": "Кольчужная рубаха",          "strength": 70,   "cost": 1150,   "emoji": "🔸", "rarity": "uncommon"},
    7:  {"name": "Ламеллярный доспех",         "strength": 95,   "cost": 2000,   "emoji": "🔸", "rarity": "rare"},
    8:  {"name": "Кожаный шлем с маской",      "strength": 125,  "cost": 2800,   "emoji": "🔸", "rarity": "rare"},
    9:  {"name": "Поножи с медными вставками", "strength": 140,  "cost": 3800,   "emoji": "🔸", "rarity": "rare"},
    10: {"name": "Рыцарская кираса",           "strength": 180,  "cost": 5300,   "emoji": "♦️", "rarity": "epic"},
    11: {"name": "Латные рукавицы",            "strength": 215,  "cost": 6500,   "emoji": "♦️", "rarity": "epic"},
    12: {"name": "Полные латные поножи",       "strength": 260,  "cost": 8200,   "emoji": "♦️", "rarity": "epic"},
    13: {"name": "Наплечники с гербом",        "strength": 325,  "cost": 11000,  "emoji": "💎", "rarity": "legendary"},
    14: {"name": "Мантия эфира",               "strength": 400,  "cost": 19500,  "emoji": "💎", "rarity": "legendary"},
    15: {"name": "Мифриловая кольчуга",        "strength": 475,  "cost": 24200,  "emoji": "💎", "rarity": "legendary"},
    16: {"name": "Шлем с рогами демона",       "strength": 580,  "cost": 34600,  "emoji": "🌟", "rarity": "mythic"},
    17: {"name": "Амулет «Каменная кожа»",     "strength": 650,  "cost": 50000,  "emoji": "🌟", "rarity": "mythic"},
    18: {"name": "Доспех из чешуи дракона",    "strength": 780,  "cost": 87000,  "emoji": "🌟", "rarity": "mythic"},
    19: {"name": "Вспышка небес",              "strength": 900,  "cost": 120000, "emoji": "🎁", "rarity": "ultra"},
    20: {"name": "Звездная мантия",            "strength": 1100, "cost": 195000, "emoji": "🎁", "rarity": "ultra"},
}

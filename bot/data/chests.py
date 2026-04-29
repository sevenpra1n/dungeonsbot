"""Chest configuration and drop tables."""

# ============== CHEST CONFIG ==============
# Формат drop-записи:
#   ("material", amount)                           — гарантированный дроп
#   ("material", (min, max))                       — гарантированный дроп в диапазоне
#   ("material", amount, chance)                   — дроп с шансом (0.0–1.0)
#   ("material", (min, max), chance)               — диапазон с шансом
#   ("status", "Название", chance)                 — разблокировать статус с шансом
#   ("experience", amount)                         — опыт профиля
#   ("experience", (min, max))                     — опыт в диапазоне
#   ("coins", (min, max))                          — монеты в диапазоне
#   ("component", "rarity", amount_or_range, chance) — компонент с шансом

CHEST_CONFIG = {
    "chest_wood": {
        "name": "Деревянный сундук",
        "emoji": "📦",
        "drop_label": "низкий",
        "drops": [
            ("coins",      (30, 100)),
            ("experience", 5),
            ("wood",       (0, 10)),
            ("food",       (4, 12)),
            ("stone",      (1, 4),   0.30),
            ("crystals",   1,        0.05),
            ("iron",       2,        0.10),
            ("copper",     (1, 3),   0.15),
            ("component",  "common", 1,       0.25),
        ],
    },
    "chest_steel": {
        "name": "Стальной сундук",
        "emoji": "🔩",
        "drop_label": "средний",
        "drops": [
            ("coins",      (50, 180)),
            ("experience", 10),
            ("wood",       (7, 13)),
            ("food",       (10, 25)),
            ("stone",      (2, 8),   0.40),
            ("crystals",   2,        0.05),
            ("iron",       (4, 10),  0.10),
            ("iron",       4),
            ("copper",     (3, 8),   0.25),
            ("status",     "Руинер", 0.08),
            ("gold",       1,        0.05),
            ("steel",      1,        0.04),
            ("component",  "common", (1, 2),  0.40),
            ("component",  "rare",   1,       0.12),
        ],
    },
    "chest_gold": {
        "name": "Золотой сундук",
        "emoji": "🌟",
        "drop_label": "высокий",
        "drops": [
            ("coins",      (150, 600)),
            ("experience", (35, 50)),
            ("wood",       (20, 75)),
            ("food",       (50, 115)),
            ("stone",      (5, 15),  0.50),
            ("crystals",   (1, 3)),
            ("crystals",   10,       0.05),
            ("iron",       (15, 25), 0.10),
            ("iron",       12),
            ("copper",     (8, 20),  0.40),
            ("status",     "Хакер",      0.02),
            ("status",     "Щедрый",     0.05),
            ("status",     "Шахтер",     0.10),
            ("status",     "Очаровашка", 0.05),
            ("gold",       3),
            ("gold",       (6, 10),  0.07),
            ("steel",      (1, 2),   0.08),
            ("amethyst",   1,        0.03),
            ("component",  "common", (2, 4),  0.60),
            ("component",  "rare",   (1, 2),  0.25),
            ("component",  "epic",   1,       0.07),
        ],
    },
    "chest_divine": {
        "name": "Всевышний сундук",
        "emoji": "👑",
        "drop_label": "очень высокий",
        "drops": [
            ("coins",      (1150, 5000)),
            ("experience", (100, 400)),
            ("wood",       (200, 450)),
            ("food",       (700, 1200)),
            ("stone",      (20, 60),   0.60),
            ("crystals",   35),
            ("crystals",   100,        0.10),
            ("iron",       200,        0.10),
            ("iron",       (80, 150)),
            ("copper",     (30, 80),   0.60),
            ("status",     "Доверие",             0.02),
            ("status",     "На богатом",          0.05),
            ("status",     "Лучший в своем деле", 0.07),
            ("status",     "Дизайнер",            0.08),
            ("gold",       (15, 50)),
            ("gold",       (30, 50),   0.07),
            ("steel",      (3, 8),     0.15),
            ("steel",      1,          0.30),
            ("amethyst",   (1, 3),     0.08),
            ("gem",        1,          0.04),
            ("component",  "common",    (3, 6),  0.80),
            ("component",  "rare",      (2, 4),  0.50),
            ("component",  "epic",      (1, 2),  0.20),
            ("component",  "legendary", 1,       0.08),
            ("component",  "mythic",    1,       0.02),
        ],
    },
}

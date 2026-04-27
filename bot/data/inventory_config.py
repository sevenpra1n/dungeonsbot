"""Inventory materials configuration.

Each entry defines the key used in the database, the display name,
and the emoji shown in messages.  Replace emoji values with
<tg-emoji emoji-id="..."> tags once you have the real IDs.
"""

from bot.data.emojis import (
    E_MAT_WOOD, E_MAT_STONE, E_MAT_FOOD, E_MAT_COPPER,
    E_MAT_IRON, E_MAT_GOLD, E_MAT_STEEL, E_MAT_AMETHYST, E_MAT_GEM,
    E_INV_HEADER, E_MARKER, E_CLIPBOARD, E_GREEN,
)

# Ordered list of materials as displayed in the inventory screen
INVENTORY_MATERIALS = [
    {
        "key":   "wood",
        "name":  "Древесина",
        "emoji": E_MAT_WOOD,
    },
    {
        "key":   "stone",
        "name":  "Камень",
        "emoji": E_MAT_STONE,
    },
    {
        "key":   "food",
        "name":  "Еда",
        "emoji": E_MAT_FOOD,
    },
    {
        "key":   "copper",
        "name":  "Медь",
        "emoji": E_MAT_COPPER,
    },
    {
        "key":   "iron",
        "name":  "Железо",
        "emoji": E_MAT_IRON,
    },
    {
        "key":   "gold",
        "name":  "Золото",
        "emoji": E_MAT_GOLD,
    },
    {
        "key":   "steel",
        "name":  "Сталь",
        "emoji": E_MAT_STEEL,
    },
    {
        "key":   "amethyst",
        "name":  "Аметист",
        "emoji": E_MAT_AMETHYST,
    },
    {
        "key":   "gem",
        "name":  "Самоцвет",
        "emoji": E_MAT_GEM,
    },
]


def format_inventory_text(materials: dict) -> str:
    """Build the full inventory message text from a materials dict.

    ``materials`` should map each material key to its current amount,
    e.g. ``{"wood": 5, "stone": 0, ...}``.
    """
    lines = [f"\n{E_CLIPBOARD} Хранение ресурсов\n"]
    for mat in INVENTORY_MATERIALS:
        amount = materials.get(mat["key"], 0)
        lines.append(
            f"{E_CLIPBOARD}|{amount}| {mat['emoji']}{mat['emoji']} {mat['name']}"
        )
    return "\n".join(lines)

"""Inventory materials configuration.

Each entry defines the key used in the database, the display name,
and the emoji shown in messages.  Replace emoji values with
<tg-emoji emoji-id="..."> tags once you have the real IDs.
"""

from bot.data.emojis import (
    E_MAT_WOOD, E_MAT_STONE, E_MAT_FOOD, E_MAT_COPPER,
    E_MAT_IRON, E_MAT_GOLD, E_MAT_STEEL, E_MAT_AMETHYST, E_MAT_GEM,
    E_INV_HEADER, E_MARKER, E_CLIPBOARD, E_GREEN,
    MD_INV_HEADER, MD_CLIPBOARD,
    MD_MAT_WOOD, MD_MAT_STONE, MD_MAT_FOOD, MD_MAT_COPPER,
    MD_MAT_IRON, MD_MAT_GOLD, MD_MAT_STEEL, MD_MAT_AMETHYST, MD_MAT_GEM,
)

# Ordered list of materials as displayed in the inventory screen
INVENTORY_MATERIALS = [
    {
        "key":      "wood",
        "name":     "Древесина",
        "emoji":    E_MAT_WOOD,
        "emoji_md": MD_MAT_WOOD,
    },
    {
        "key":      "stone",
        "name":     "Камень",
        "emoji":    E_MAT_STONE,
        "emoji_md": MD_MAT_STONE,
    },
    {
        "key":      "food",
        "name":     "Еда",
        "emoji":    E_MAT_FOOD,
        "emoji_md": MD_MAT_FOOD,
    },
    {
        "key":      "copper",
        "name":     "Медь",
        "emoji":    E_MAT_COPPER,
        "emoji_md": MD_MAT_COPPER,
    },
    {
        "key":      "iron",
        "name":     "Железо",
        "emoji":    E_MAT_IRON,
        "emoji_md": MD_MAT_IRON,
    },
    {
        "key":      "gold",
        "name":     "Золото",
        "emoji":    E_MAT_GOLD,
        "emoji_md": MD_MAT_GOLD,
    },
    {
        "key":      "steel",
        "name":     "Сталь",
        "emoji":    E_MAT_STEEL,
        "emoji_md": MD_MAT_STEEL,
    },
    {
        "key":      "amethyst",
        "name":     "Аметист",
        "emoji":    E_MAT_AMETHYST,
        "emoji_md": MD_MAT_AMETHYST,
    },
    {
        "key":      "gem",
        "name":     "Самоцвет",
        "emoji":    E_MAT_GEM,
        "emoji_md": MD_MAT_GEM,
    },
]


def format_inventory_text(materials: dict) -> str:
    """Build the inventory message text in MarkdownV2 format.

    ``materials`` should map each material key to its current amount,
    e.g. ``{"wood": 5, "stone": 0, ...}``.
    """
    lines = [f"\n{MD_CLIPBOARD} Хранение ресурсов\n"]
    for mat in INVENTORY_MATERIALS:
        amount = materials.get(mat["key"], 0)
        em = mat["emoji_md"]
        lines.append(
            f"{MD_CLIPBOARD}\\|{amount}\\|{em}{em} {mat['name']}"
        )
    return "\n".join(lines)

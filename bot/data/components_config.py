"""Components (crafting parts) configuration by rarity tier.

Replace emoji values with <tg-emoji emoji-id="..."> tags once you have
the real Telegram custom-emoji IDs.
"""

from bot.data.emojis import (
    E_COMP_HEADER, E_COMP_BOX,
    E_RARITY_COMMON, E_RARITY_RARE, E_RARITY_EPIC,
    E_RARITY_LEGENDARY, E_RARITY_MYTHIC,
    E_CALENDAR, E_CLIPBOARD, E_YELLOW,
)

# Ordered list of component rarity tiers
COMPONENT_RARITIES = [
    {
        "key":          "common",
        "name":         "обычная",
        "rarity_emoji": E_RARITY_COMMON,
    },
    {
        "key":          "rare",
        "name":         "редкая",
        "rarity_emoji": E_RARITY_RARE,
    },
    {
        "key":          "epic",
        "name":         "эпическая",
        "rarity_emoji": E_RARITY_EPIC,
    },
    {
        "key":          "legendary",
        "name":         "легендарная",
        "rarity_emoji": E_RARITY_LEGENDARY,
    },
    {
        "key":          "mythic",
        "name":         "мифическая",
        "rarity_emoji": E_RARITY_MYTHIC,
    },
]


def format_components_text(comp: dict, total: int) -> str:
    """Build the components message text.

    ``comp`` maps rarity key → amount, e.g. ``{"common": 3, "rare": 0, ...}``.
    ``total`` is the pre-computed sum of all components.
    """
    text = f"{E_COMP_HEADER} Компоненты:\n\n{total} {E_COMP_BOX} Компоненты\n"
    for rarity in COMPONENT_RARITIES:
        amount = comp.get(rarity["key"], 0)
        text += (
            f"\n├ {E_CALENDAR} Редкость:{rarity['rarity_emoji']}{rarity['name']}\n"
            f"├ {E_CLIPBOARD} количество: {amount} {E_YELLOW}\n"
        )
    return text

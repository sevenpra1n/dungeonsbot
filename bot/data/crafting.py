"""Crafting recipes configuration for component manufacturing."""

# Material display info for crafting menus (MarkdownV2 format)
_E_MARKER    = '![▫️](tg://emoji?id=5267324424113124134)'
_E_WARN      = '![⚠️](tg://emoji?id=5276240711795107620)'
_E_GEAR      = '![⚙️](tg://emoji?id=5398095118735521227)'
_E_BOX_HDR   = '![📦](tg://emoji?id=5278540791336165644)'
_E_HASHTAG   = r'![\#️⃣](tg://emoji?id=5354857360844152098)'
_E_CHART     = '![📊](tg://emoji?id=5278778882848220741)'
_E_BOX_REQ   = '![📦](tg://emoji?id=5206702193385700709)'
_E_CLOCK     = '![🕓](tg://emoji?id=5276412364458059956)'
_E_YELLOW    = '![🟡](tg://emoji?id=5906800644525660990)'
_E_GREEN     = '![🟢](tg://emoji?id=5906852613629941703)'
_E_RED       = '![🔴](tg://emoji?id=5907027122446145395)'

_RARITY_EMOJIS = {
    "common":    '![🌟](tg://emoji?id=5395855331945392566)',
    "rare":      '![🌟](tg://emoji?id=5395316601312548706)',
    "epic":      '![🌟](tg://emoji?id=5395550054259921224)',
    "legendary": '![🌟](tg://emoji?id=5395487888903280719)',
    "mythic":    '![🌟](tg://emoji?id=5395620513198410698)',
}

_MAT_EMOJIS = {
    "wood":     '![🌳](tg://emoji?id=5449918202718985124)',
    "stone":    '![🪨](tg://emoji?id=5433955200849159326)',
    "copper":   '![🔶](tg://emoji?id=6278264420267201893)',
    "iron":     '![⛰](tg://emoji?id=6278216436892570592)',
    "gold":     '![🥇](tg://emoji?id=6280721566762277148)',
    "steel":    '![🌋](tg://emoji?id=6280349132968168995)',
    "amethyst": '![🤩](tg://emoji?id=5341757074936193080)',
    "gem":      '![🎁](tg://emoji?id=5429387443000341439)',
}

_MAT_NAMES = {
    "wood":     "дерева",
    "stone":    "камня",
    "copper":   "меди",
    "iron":     "железа",
    "gold":     "золота",
    "steel":    "стали",
    "amethyst": "аметиста",
    "gem":      "самоцвета",
}

CRAFTING_RECIPES = {
    "common": {
        "name": "Обычный компонент",
        "rarity_emoji": '![🌟](tg://emoji?id=5395855331945392566)',
        "craft_chance": 0.70,
        "materials": {
            "wood": 40,
        },
        "experience": (2, 5),
    },
    "rare": {
        "name": "Редкий компонент",
        "rarity_emoji": '![🌟](tg://emoji?id=5395316601312548706)',
        "craft_chance": 0.65,
        "materials": {
            "wood": 65,
            "stone": 30,
            "copper": 15,
            "iron": 6,
        },
        "experience": (4, 8),
    },
    "epic": {
        "name": "Эпический компонент",
        "rarity_emoji": '![🌟](tg://emoji?id=5395550054259921224)',
        "craft_chance": 0.55,
        "materials": {
            "wood": 95,
            "stone": 65,
            "copper": 28,
            "iron": 10,
            "gold": 2,
        },
        "experience": (6, 12),
    },
    "legendary": {
        "name": "Легендарный компонент",
        "rarity_emoji": '![🌟](tg://emoji?id=5395487888903280719)',
        "craft_chance": 0.40,
        "materials": {
            "wood": 145,
            "stone": 100,
            "copper": 40,
            "iron": 26,
            "gold": 8,
            "steel": 2,
        },
        "experience": (8, 16),
    },
    "mythic": {
        "name": "Мифический компонент",
        "rarity_emoji": '![🌟](tg://emoji?id=5395620513198410698)',
        "craft_chance": 0.25,
        "materials": {
            "wood": 300,
            "stone": 150,
            "copper": 95,
            "iron": 70,
            "gold": 16,
            "steel": 6,
            "amethyst": 4,
            "gem": 1,
        },
        "experience": (10, 20),
    },
}

# Display names for rarity keys used in component names (for buttons)
RARITY_DISPLAY_NAMES = {
    "common":    "обычный",
    "rare":      "редкий",
    "epic":      "эпический",
    "legendary": "легендарный",
    "mythic":    "мифический",
}

# Component rarity names (feminine form, matches components_config)
RARITY_COMPONENT_NAMES = {
    "common":    "обычная",
    "rare":      "редкая",
    "epic":      "эпическая",
    "legendary": "легендарная",
    "mythic":    "мифическая",
}


def format_crafting_menu_text(comp: dict) -> str:
    """Build the crafting menu text showing player's current components and all recipes."""
    lines = [
        f"{_E_BOX_HDR}{_E_GEAR} Изготовление компонентов:\n",
        f"{_E_HASHTAG} Ваши компоненты:",
    ]
    for rarity_key, comp_name in RARITY_COMPONENT_NAMES.items():
        rarity_emoji = _RARITY_EMOJIS[rarity_key]
        amount = comp.get(rarity_key, 0)
        lines.append(f"{_E_MARKER}{rarity_emoji}{comp_name} \\({amount}\\){_E_YELLOW}")
    lines.append(f"\n{_E_CHART} Ниже можете изготовить их\\!")
    return "\n".join(lines)


def format_crafting_choice_menu() -> str:
    """Build the crafting choice menu text showing all recipes with requirements."""
    lines = [
        f"{_E_WARN}{_E_GEAR} Выберите что хотите изготовить!\n",
    ]
    for rarity_key, recipe in CRAFTING_RECIPES.items():
        rarity_emoji = recipe["rarity_emoji"]
        lines.append(f"{_E_MARKER}{rarity_emoji} {recipe['name']}:")
        lines.append(f"{_E_BOX_REQ} Требуется:")
        for mat, amount in recipe["materials"].items():
            mat_emoji = _MAT_EMOJIS.get(mat, "")
            mat_name = _MAT_NAMES.get(mat, mat)
            lines.append(f"{_E_MARKER}{mat_emoji} {amount} {mat_name}")
        chance_pct = int(recipe["craft_chance"] * 100)
        lines.append(f"\\({_E_CLOCK} шанс крафта: {chance_pct}%\\)\n")
    return "\n".join(lines)


def format_craft_result(rarity_key: str, success: bool, exp_gained: int) -> str:
    """Build the craft result message."""
    recipe = CRAFTING_RECIPES[rarity_key]
    rarity_emoji = recipe["rarity_emoji"]
    comp_name = recipe["name"]
    if success:
        return (
            f"{_E_GREEN} Крафт успешен!\n\n"
            f"{_E_MARKER}{rarity_emoji} {comp_name} добавлен в инвентарь\\!\n"
            f"{_E_MARKER}Получено опыта: {exp_gained}"
        )
    else:
        return (
            f"{_E_RED} Крафт провалился\\!\n\n"
            f"{_E_MARKER}{rarity_emoji} {comp_name} не получен\\.\n"
            f"{_E_MARKER}Ресурсы потрачены\\."
        )

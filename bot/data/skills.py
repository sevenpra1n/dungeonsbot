"""Skills data constants."""

# ============== SKILLS ==============
SKILLS = {
    1: {
        "name": "Мега-молот",
        "emoji": "✨",
        "desc": "Наносит 70% урона, шанс 35% заставить врага пропустить ход",
        "damage_mult": 0.7,
        "stun_chance": 0.35,
        "mana_cost": 30,
        "price": 1200,
    },
    2: {
        "name": "Кровавое неистовство",
        "emoji": "✨",
        "desc": "Наносит 2x урона, но вы теряете 15% от максимального HP",
        "damage_mult": 2.0,
        "hp_loss_pct": 0.15,
        "mana_cost": 50,
        "price": 2500,
    },
    3: {
        "name": "Ослепляющая вспышка",
        "emoji": "✨",
        "desc": "Снижает точность врага на 50% на 2 хода",
        "blind_turns": 2,
        "miss_chance_add": 0.5,
        "mana_cost": 100,
        "price": 7500,
    },
}

"""Status definitions and helper functions."""

from bot.config import BAGOUSER_ID
from bot.database import get_friends_count

# ============== STATUS SYSTEM ==============
STATUSES = {
    1: {"name": "Новичок",      "emoji": "🔸", "custom_emoji": '<tg-emoji emoji-id="5323718538710491847">🔸</tg-emoji>', "required_level": 1,  "type": "default"},
    2: {"name": "Продвинутый",  "emoji": "🌱", "custom_emoji": '<tg-emoji emoji-id="5343920308229256142">🌱</tg-emoji>', "required_level": 5,  "type": "unlock_level"},
    3: {"name": "Охотник",      "emoji": "🔪", "custom_emoji": '<tg-emoji emoji-id="5224460534534916102">🔪</tg-emoji>', "required_level": 1,  "type": "free"},
    4: {"name": "Любитель PVP", "emoji": "⚔️", "custom_emoji": '<tg-emoji emoji-id="5454014806950429357">⚔️</tg-emoji>', "required_level": 1,  "type": "free"},
    5: {"name": "Добытчик",     "emoji": "🥇", "custom_emoji": '<tg-emoji emoji-id="6278187557532472415">🥇</tg-emoji>', "required_level": 1,  "type": "free"},
    # Page 2 - new statuses
    6:  {"name": "Сердцеед",     "emoji": "❤️", "custom_emoji": '<tg-emoji emoji-id="5355174247826217637">❤️</tg-emoji>', "required_level": 1, "type": "unlock_friends", "required_friends": 1},
    7:  {"name": "Стиляга",      "emoji": "👓", "custom_emoji": '<tg-emoji emoji-id="5834901642155137299">👓</tg-emoji>', "required_level": 1, "type": "unlock_strength", "required_strength": 200},
    8:  {"name": "Press F",      "emoji": "⚰️", "custom_emoji": '<tg-emoji emoji-id="5938394329465756346">🎁</tg-emoji>', "required_level": 1, "type": "unlock_deaths", "required_deaths": 20},
    9:  {"name": "Лидер",        "emoji": "👑", "custom_emoji": '<tg-emoji emoji-id="5936238625250350064">🎁</tg-emoji>', "required_level": 1, "type": "unlock_strength", "required_strength": 1000},
    10: {"name": "Удачливый",    "emoji": "🍀", "custom_emoji": '<tg-emoji emoji-id="5960593366151337910">🎁</tg-emoji>', "required_level": 1, "type": "unlock_dodges", "required_dodges": 30},
    # Page 3 - new statuses
    11: {"name": "Гладиатор",    "emoji": "🏛", "custom_emoji": '<tg-emoji emoji-id="6001349144046737619">🎁</tg-emoji>', "required_level": 1, "type": "unlock_pve_wins", "required_pve_wins": 50},
    12: {"name": "Убийца",       "emoji": "👹", "custom_emoji": '<tg-emoji emoji-id="5796297917752941521">👹</tg-emoji>', "required_level": 1, "type": "unlock_pve_wins", "required_pve_wins": 120},
    13: {"name": "Творчество",   "emoji": "🎨", "custom_emoji": '<tg-emoji emoji-id="6021462012037437193">🎁</tg-emoji>', "required_level": 1, "type": "unlock_clan_image"},
    14: {"name": "Пример для подражания", "emoji": "🌠", "custom_emoji": '<tg-emoji emoji-id="6021486768228940485">🎁</tg-emoji>', "required_level": 1, "type": "unlock_strength", "required_strength": 2000},
    15: {"name": "Какашка",      "emoji": "💩", "custom_emoji": '<tg-emoji emoji-id="6005662304824203821">💩</tg-emoji>', "required_level": 1, "type": "unlock_spam"},
    16: {"name": "багоюзер 777", "emoji": "💎", "custom_emoji": '<tg-emoji emoji-id="5354902509540370798">💎</tg-emoji>', "required_level": 1, "type": "unlock_bagouser"},
    # Page 4 - chest statuses
    17: {"name": "Руинер",                "emoji": "💣", "custom_emoji": '<tg-emoji emoji-id="5886484710481205789">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    18: {"name": "Хакер",                 "emoji": "💻", "custom_emoji": '<tg-emoji emoji-id="6021412890496473421">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    19: {"name": "Щедрый",                "emoji": "🤲", "custom_emoji": '<tg-emoji emoji-id="6001349144046737619">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    20: {"name": "Шахтер",                "emoji": "⛏️", "custom_emoji": '<tg-emoji emoji-id="5456456455634370613">⛏️</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    21: {"name": "Очаровашка",            "emoji": "✨", "custom_emoji": '<tg-emoji emoji-id="5938394329465756346">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    22: {"name": "Доверие",               "emoji": "🤝", "custom_emoji": '<tg-emoji emoji-id="6021462012037437193">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    23: {"name": "На богатом",            "emoji": "💰", "custom_emoji": '<tg-emoji emoji-id="6021486768228940485">🎁</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    24: {"name": "Лучший в своем деле",   "emoji": "🏆", "custom_emoji": '<tg-emoji emoji-id="5312315739842026755">🏆</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
    25: {"name": "Дизайнер",              "emoji": "🎨", "custom_emoji": '<tg-emoji emoji-id="5222021318378948590">🎨</tg-emoji>', "required_level": 1, "type": "unlock_chest"},
}

STATUSES_PER_PAGE = 5


def is_status_available(player: dict, status_info: dict) -> bool:
    """Проверить, доступен ли статус для игрока"""
    s_type = status_info.get("type", "default")
    if s_type in ("default", "free"):
        return True
    if s_type == "unlock_level":
        return player.get('player_level', 1) >= status_info.get('required_level', 1)
    if s_type == "unlock_matches":
        return player.get('online_matches', 0) >= (status_info.get('required_matches', 0) or 0)
    if s_type == "unlock_friends":
        friends_count = get_friends_count(player['user_id'])
        return friends_count >= status_info.get('required_friends', 1)
    if s_type == "unlock_strength":
        return player.get('strength', 0) >= status_info.get('required_strength', 0)
    if s_type == "unlock_deaths":
        return player.get('deaths', 0) >= status_info.get('required_deaths', 0)
    if s_type == "unlock_dodges":
        return player.get('dodges', 0) >= status_info.get('required_dodges', 0)
    if s_type == "unlock_pve_wins":
        return player.get('pve_wins', 0) >= status_info.get('required_pve_wins', 0)
    if s_type == "unlock_clan_image":
        return player.get('has_set_clan_image', 0) >= 1
    if s_type == "unlock_spam":
        return player.get('is_spammer', 0) >= 1
    if s_type == "unlock_bagouser":
        return player.get('user_id') == BAGOUSER_ID
    if s_type == "unlock_chest":
        return player.get('_chest_unlocked_' + status_info.get('name', ''), False)
    return False


def _get_status_requirement_text(status_info: dict) -> str:
    """Получить текст условия для заблокированного статуса"""
    s_type = status_info.get("type", "default")
    if s_type == "unlock_level":
        return f"🔒 Ур.{status_info.get('required_level', 1)}"
    if s_type == "unlock_friends":
        return f"🔒 Друзья: {status_info.get('required_friends', 1)}"
    if s_type == "unlock_strength":
        return f"🔒 Сила: {status_info.get('required_strength', 0)}+"
    if s_type == "unlock_deaths":
        return f"🔒 Смертей: {status_info.get('required_deaths', 0)}"
    if s_type == "unlock_dodges":
        return f"🔒 Уворотов: {status_info.get('required_dodges', 0)}"
    if s_type == "unlock_pve_wins":
        return f"🔒 PvE побед: {status_info.get('required_pve_wins', 0)}"
    if s_type == "unlock_clan_image":
        return "🔒 Картина в клане"
    if s_type == "unlock_spam":
        return "🔒 Спам в чате клана"
    if s_type == "unlock_bagouser":
        return "🔒 Особый"
    if s_type == "unlock_chest":
        return "🔒 Можно найти в сундуке"
    return "🔒"


def _format_statuses_text(player: dict, page: int = 0) -> str:
    """Форматировать текст списка статусов с пагинацией"""
    all_ids = sorted(STATUSES.keys())
    total_pages = max(1, (len(all_ids) + STATUSES_PER_PAGE - 1) // STATUSES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * STATUSES_PER_PAGE
    end = start + STATUSES_PER_PAGE
    page_ids = all_ids[start:end]

    # Count unlocked statuses
    unlocked_count = sum(1 for s_id in all_ids if is_status_available(player, STATUSES[s_id]))

    text = f"🎭 <b>СТАТУСЫ</b> ({unlocked_count}/{len(all_ids)})\nСтраница {page + 1}/{total_pages}\n\nВыбери статус для своего персонажа:\n\n"
    for s_id in page_ids:
        s = STATUSES[s_id]
        can = is_status_available(player, s)
        owned = (player.get('status') == s['name'])
        lock = "" if can else f" {_get_status_requirement_text(s)}"
        check = " ✅" if owned else ""
        text += f"{s.get('custom_emoji', s['emoji'])} | {s['name']}{lock}{check}\n"
    return text

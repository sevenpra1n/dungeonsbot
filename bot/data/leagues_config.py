"""Rating league configuration.

Defines thresholds, win/loss points and display emoji for every league.
Replace emoji values with <tg-emoji emoji-id="..."> tags once you have
the real Telegram custom-emoji IDs.
"""

from bot.data.emojis import (
    E_LEAGUE_NEWBIE, E_LEAGUE_SILVER, E_LEAGUE_AMATEUR,
    E_LEAGUE_ADVANCED, E_LEAGUE_CHOSEN, E_LEAGUE_PRO,
    E_LEAGUE_ESPORTS, E_LEAGUE_WORLD,
    E_MARKER, E_PLUS, E_MINUS,
)

# Each entry is ordered from lowest to highest threshold.
# ``min_points`` is the inclusive lower bound.
# ``max_points`` is the exclusive upper bound (None = no upper limit).
LEAGUES = [
    {
        "key":        "newbie",
        "name":       "Новичковая",
        "emoji":      E_LEAGUE_NEWBIE,
        "min_points": 0,
        "max_points": 100,
        "win_points": 12,
        "loss_points": 3,
    },
    {
        "key":        "silver",
        "name":       "Серебряная",
        "emoji":      E_LEAGUE_SILVER,
        "min_points": 100,
        "max_points": 200,
        "win_points": 10,
        "loss_points": 4,
    },
    {
        "key":        "amateur",
        "name":       "Любительская",
        "emoji":      E_LEAGUE_AMATEUR,
        "min_points": 200,
        "max_points": 350,
        "win_points": 10,
        "loss_points": 4,
    },
    {
        "key":        "advanced",
        "name":       "Продвинутая",
        "emoji":      E_LEAGUE_ADVANCED,
        "min_points": 350,
        "max_points": 500,
        "win_points": 9,
        "loss_points": 5,
    },
    {
        "key":        "chosen",
        "name":       "Избранная",
        "emoji":      E_LEAGUE_CHOSEN,
        "min_points": 500,
        "max_points": 800,
        "win_points": 8,
        "loss_points": 6,
    },
    {
        "key":        "pro",
        "name":       "Профессиональная",
        "emoji":      E_LEAGUE_PRO,
        "min_points": 800,
        "max_points": 1150,
        "win_points": 8,
        "loss_points": 7,
    },
    {
        "key":        "esports",
        "name":       "Киберспортивная",
        "emoji":      E_LEAGUE_ESPORTS,
        "min_points": 1150,
        "max_points": 1500,
        "win_points": 7,
        "loss_points": 9,
    },
    {
        "key":        "world",
        "name":       "Мировая",
        "emoji":      E_LEAGUE_WORLD,
        "min_points": 1500,
        "max_points": None,
        "win_points": 5,
        "loss_points": 11,
    },
]


def get_league(rating_points: int) -> dict:
    """Return the league dict that matches the given rating points."""
    for league in reversed(LEAGUES):
        if rating_points >= league["min_points"]:
            return league
    return LEAGUES[0]


def get_league_label(rating_points: int) -> str:
    """Return the formatted league string used in profile / rating messages."""
    league = get_league(rating_points)
    return f"{league['emoji']} {league['name']} лига"


def get_league_points(rating_points: int) -> tuple:
    """Return (win_points, loss_points) for the current league."""
    league = get_league(rating_points)
    return league["win_points"], league["loss_points"]


def format_all_leagues_info() -> str:
    """Build the full leagues-info block shown in the «О лигах» screen."""
    lines = [f"{E_MARKER} О лигах:\n"]
    for league in LEAGUES:
        max_str = str(league["max_points"]) if league["max_points"] is not None else "∞"
        threshold = f"(порог {league['min_points']}-{max_str} points)"
        lines.append(
            f"\n{league['emoji']} {league['name']} лига:\n"
            f"{threshold}\n"
            f"{E_PLUS} {league['win_points']} points за победу\n"
            f"{E_MINUS} {league['loss_points']} points за поражение\n"
        )
    return "".join(lines)


def format_league_info(rating_points: int) -> str:
    """Build a detailed league info block (used in league-info screens)."""
    league = get_league(rating_points)
    max_str = (
        f"{league['max_points']}" if league["max_points"] is not None else "∞"
    )
    threshold = f"(порог {league['min_points']}-{max_str} points)"
    return (
        f"{E_MARKER}{league['emoji']} {league['name']} лига:\n"
        f"{threshold}\n"
        f"{E_PLUS} {league['win_points']} points за победу\n"
        f"{E_MINUS} {league['loss_points']} points за поражение"
    )

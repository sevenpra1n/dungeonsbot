"""Data package for game constants and configuration."""

from bot.data import emojis          # noqa: F401  – emoji constants
from bot.data import inventory_config as inventory   # noqa: F401
from bot.data import components_config as components  # noqa: F401
from bot.data import leagues_config as leagues        # noqa: F401

# Convenience re-exports so callers can do:
#   from bot.data import INVENTORY_MATERIALS, COMPONENT_RARITIES, LEAGUES
from bot.data.inventory_config import INVENTORY_MATERIALS     # noqa: F401
from bot.data.components_config import COMPONENT_RARITIES     # noqa: F401
from bot.data.leagues_config import (                         # noqa: F401
    LEAGUES,
    get_league,
    get_league_label,
    get_league_points,
    format_league_info,
)

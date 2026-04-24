"""Data package for game constants and configuration."""

from bot.data import emojis                                    # noqa: F401
from bot.data import inventory_config as inventory             # noqa: F401
from bot.data import components_config as components           # noqa: F401
from bot.data import leagues_config as leagues                 # noqa: F401
from bot.data import chests_config as chests                   # noqa: F401
from bot.data import likes_config as likes                     # noqa: F401

# Convenience re-exports
from bot.data.inventory_config import INVENTORY_MATERIALS      # noqa: F401
from bot.data.components_config import COMPONENT_RARITIES      # noqa: F401
from bot.data.leagues_config import (                          # noqa: F401
    LEAGUES,
    get_league,
    get_league_label,
    get_league_points,
    format_league_info,
    format_all_leagues_info,
)
from bot.data.chests_config import (                           # noqa: F401
    CHEST_DISPLAY,
    OPENING_STEPS,
    format_chest_opening,
    format_chest_reward,
)
from bot.data.likes_config import (                            # noqa: F401
    format_like_notification,
    format_likes_count,
)

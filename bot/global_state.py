"""Global mutable state shared across handlers (cooldowns, queues, sessions)."""

from datetime import datetime

# Словарь для отслеживания cooldown боевых действий (2 сек)
battle_cooldowns: dict = {}

# Очередь поиска PvP: user_id -> {nickname, strength, wins, chat_id}
pvp_queue: dict = {}
# Активные PvP пары: user_id -> opponent_user_id
pvp_pairs: dict = {}

# CO-OP рейд: ожидающие приглашения target_user_id -> {inviter_id, inviter_nickname, inviter_chat_id}
coop_raid_invites: dict = {}
# CO-OP рейд: подтверждённые пары (лобби) user_id -> partner_id (двунаправленное)
coop_raid_pairs: dict = {}

# Активные сессии клан-чата: clan_id -> set(user_id)
clan_chat_sessions: dict = {}

# Трекер сообщений в чате клана для детекции спама: user_id -> list of timestamps
clan_chat_spam_tracker: dict = {}

# Cache for Telegram file_id by image path (avoids re-uploading)
image_file_id_cache: dict = {}

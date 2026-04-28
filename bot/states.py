"""FSM state groups for all bot menus and flows."""

from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_nickname = State()

class EquipmentMenu(StatesGroup):
    viewing_equipment = State()

class ForgeMenu(StatesGroup):
    viewing_forge = State()
    viewing_weapons = State()
    viewing_armor = State()
    viewing_skills = State()
    viewing_crafting = State()
    viewing_craft_choice = State()

class BattleState(StatesGroup):
    viewing_enemies = State()
    in_battle = State()
    enemy_attacking = State()
    battle_round = State()

class RaidState(StatesGroup):
    viewing_menu = State()
    in_raid = State()

class OnlineState(StatesGroup):
    viewing_menu = State()
    searching = State()
    waiting_accept = State()
    in_pvp_battle = State()

class ClanMenu(StatesGroup):
    viewing_clans = State()
    creating_clan_confirm = State()
    creating_clan_name = State()
    creating_clan_description = State()
    viewing_my_clan = State()
    kicking_member = State()
    changing_min_power = State()
    deleting_clan_confirm = State()
    promoting_member = State()
    demoting_member = State()
    in_clan_chat = State()
    selecting_clan_customization = State()
    changing_clan_name = State()
    changing_clan_description = State()
    changing_clan_image = State()

class AdminPanel(StatesGroup):
    main_menu = State()
    adding_coins_nickname = State()
    adding_coins_amount = State()
    adding_strength_nickname = State()
    adding_strength_amount = State()
    adding_experience_nickname = State()
    adding_experience_amount = State()
    adding_crystals_nickname = State()
    adding_crystals_amount = State()
    adding_raid_tickets_nickname = State()
    adding_raid_tickets_amount = State()
    adding_materials_nickname = State()
    adding_materials_amount = State()
    adding_boss_tickets_nickname = State()
    adding_boss_tickets_amount = State()
    adding_chests_nickname = State()
    adding_chests_type = State()
    adding_chests_amount = State()
    adding_components_nickname = State()
    adding_components_amount = State()

class LocationMenu(StatesGroup):
    viewing_map = State()
    viewing_location = State()
    searching_enemy = State()

class ProfileMenu(StatesGroup):
    viewing_profile = State()
    viewing_statuses = State()
    viewing_settings = State()
    confirming_delete_data = State()
    waiting_delete_data_confirm = State()
    viewing_inventory = State()
    viewing_components = State()
    viewing_chests = State()
    opening_chest = State()
    changing_nickname = State()
    changing_profile_photo = State()


class TutorialState(StatesGroup):
    welcome = State()
    entering_nickname = State()

class MarketMenu(StatesGroup):
    viewing_category = State()
    viewing_market = State()
    selling_resource = State()
    buying_ticket = State()
    viewing_consumables = State()
    viewing_items = State()

class RatingState(StatesGroup):
    viewing_rating = State()
    viewing_player = State()

class FriendsMenu(StatesGroup):
    viewing_friends = State()
    viewing_requests = State()
    viewing_friend_profile = State()

class ClanBossState(StatesGroup):
    viewing_menu = State()
    in_battle = State()
    battle_round = State()

class CoopRaidState(StatesGroup):
    waiting_invite = State()   # Приглашённый игрок решает принять/отклонить
    in_lobby = State()         # Принявший ожидает старта от организатора
    in_raid = State()          # Оба игрока в активном CO-OP рейде

class LikeState(StatesGroup):
    waiting_message_from_rating = State()  # Ввод послания при лайке из рейтинга
    waiting_message_from_friend = State()  # Ввод послания при лайке из профиля друга

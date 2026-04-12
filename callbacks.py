from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import bott

router = Router()

@router.callback_query(F.data.startswith("main_"))
async def handle_main_menu(query: types.CallbackQuery, state: FSMContext):
    """Обработка нажатий inline-кнопок главного меню"""
    await query.answer()

    action = query.data.replace("main_", "")
    message = query.message
    # query.message.from_user — это бот, подменяем на реального пользователя
    message.from_user = query.from_user

    # Вызываем соответствующие функции
    if action == "map":
        await bott.open_map(message, state)
    elif action == "inventory":
        await bott.open_inventory_main(message, state)
    elif action == "forge":
        await bott.open_forge(message, state)
    elif action == "raid":
        await bott.open_raid(message, state)
    elif action == "online":
        await bott.open_online(message, state)
    elif action == "clans":
        await bott.open_clans(message, state)
    elif action == "leaderboard":
        await bott.show_leaderboard(message)
    elif action == "profile":
        await bott.show_profile(message, state)
    elif action == "market":
        await bott.open_market(message, state)

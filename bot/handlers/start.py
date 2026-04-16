from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states import Registration
from bot.database import get_player, add_player
from bot.utils import send_image_with_text
from bot.keyboards import show_main_menu, get_main_menu_text, get_main_kb

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    
    if player:
        await send_image_with_text(message, "images/menu.png", get_main_menu_text(), reply_markup=get_main_kb())
    else:
        await message.answer("Привет! Давай начнем. Как тебя будут звать в игре? Введи свой никнейм:")
        await state.set_state(Registration.waiting_for_nickname)

@router.message(Registration.waiting_for_nickname)
async def process_nickname(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    nickname = message.text.strip() if message.text else ""

    if not nickname or len(nickname) > 32:
        await message.answer("❌ Никнейм должен быть от 1 до 32 символов. Попробуй ещё раз:")
        return

    add_player(user_id, nickname)
    
    await state.clear()
    await message.answer(f"Приятно познакомиться, {nickname}! Теперь ты можешь приступать.")
    await send_image_with_text(message, "images/menu.png", get_main_menu_text(), reply_markup=get_main_kb())

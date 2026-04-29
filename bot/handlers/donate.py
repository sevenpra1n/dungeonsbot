"""Handlers for the donate/payment system and admin payment panel."""

import html
import logging

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.loader import bot
from bot.config import ADMIN_IDS
from bot.emojis import (
    E_TAG, E_DOLLAR, E_GREEDY, E_YELLOW, E_SQ, E_COINS, E_CRYSTALS,
    E_CHECK_G, E_LINK_D, E_BANK, E_CODER, E_WALLET, E_GREEN2, E_RUBLE,
    E_BAN, D_COIN_1, D_COIN_2, D_COIN_3, D_COIN_4, D_COIN_5,
    D_CRYS_1, D_CRYS_2, D_CRYS_3, D_CRYS_4, D_CRYS_5,
    E_CROSS, E_GIFT,
)
from bot.states import DonateMenu, AdminPaymentPanel
from bot.database import (
    get_player, get_player_real_balance,
    create_donation_order, get_donation_order,
    get_pending_donation_orders, update_donation_order_status,
    add_real_balance, deduct_real_balance,
    add_coins_to_player, add_crystals_to_player,
)
from bot.keyboards import (
    get_market_category_kb,
    get_donate_coins_kb, get_donate_crystals_kb,
    get_payment_waiting_kb,
    get_admin_payment_kb, get_admin_order_action_kb,
    DONATE_COINS_PRICES, DONATE_CRYSTALS_PRICES,
)
from bot.utils import send_image_with_text

router = Router()
logger = logging.getLogger(__name__)

# ============== TEXT BUILDERS ==============

def _donate_coins_text(balance: int) -> str:
    return (
        f"{E_TAG}{E_DOLLAR} <b>Донат:</b>\n\n"
        f"{D_COIN_1}{D_COIN_2}{D_COIN_3}{D_COIN_4}{D_COIN_5}\n"
        f"{E_YELLOW} Ваш баланс: {balance} {E_GREEDY}\n\n"
        f"{E_SQ}1.000{E_COINS} = 19{E_RUBLE}\n"
        f"{E_SQ}5.000{E_COINS} = 89{E_RUBLE}\n"
        f"{E_SQ}20.000{E_COINS} = 309{E_RUBLE}\n"
        f"{E_SQ}80.000{E_COINS} = 1199{E_RUBLE}"
    )


def _donate_crystals_text(balance: int) -> str:
    return (
        f"{E_TAG}{E_DOLLAR} <b>Донат:</b>\n\n"
        f"{D_CRYS_1}{D_CRYS_2}{D_CRYS_3}{D_CRYS_4}{D_CRYS_5}\n"
        f"{E_YELLOW} Ваш баланс: {balance} {E_GREEDY}\n\n"
        f"{E_SQ}79{E_CRYSTALS} = 39{E_RUBLE}\n"
        f"{E_SQ}239{E_CRYSTALS} = 99{E_RUBLE}({E_GIFT}Выгодно!)\n"
        f"{E_SQ}829{E_CRYSTALS} = 319{E_RUBLE}\n"
        f"{E_SQ}2.999{E_CRYSTALS} = 1029{E_RUBLE}"
    )


def _insufficient_funds_text(required: int, balance: int) -> str:
    return (
        f"{E_TAG} {E_BAN} <b>Вам не хватает средств для оплаты!</b>\n\n"
        f"{E_CHECK_G} Необходимо: {required} {E_GREEDY}\n"
        f"{E_WALLET} Ваш баланс: {balance} {E_GREEDY}\n\n"
        f"{E_SQ}Пополнить баланс можно по кнопке ниже:"
    )


def _lot_created_text(amount: int, memo: str) -> str:
    return (
        f"{E_GREEN2} <b>Лот зарезервирован!</b>\n\n"
        f"{E_CHECK_G} Сумма пополнения: {amount} {E_GREEDY}\n"
        f"{E_YELLOW} Код memo: <code>{memo}</code>\n\n"
        f"{E_LINK_D} Приложите при оплате этот код в комментарии при оплате.\n"
        f"{E_SQ}{E_BANK} Номер отправки:\n"
        f"{E_SQ}+7 993 783 93 70 (ВТБ)\n\n"
        f"{E_CODER} После оплаты в течение нескольких минут, сумма будет начислена!\n"
        f"(Не забудьте после оплаты нажать \"Оплатил(а)\")"
    )


def _admin_notify_new_order_text(nickname: str, amount: int, memo: str, order_id: int) -> str:
    return (
        f"🔔 <b>Новая заявка на пополнение!</b>\n\n"
        f"👤 Игрок: <b>{html.escape(nickname)}</b>\n"
        f"💰 Сумма: <b>{amount}₽</b>\n"
        f"📝 Memo: <code>{memo}</code>\n"
        f"🆔 Заявка №{order_id}\n\n"
        f"Откройте /admin для управления заявками."
    )


def _admin_notify_paid_text(nickname: str, amount: int, memo: str, order_id: int) -> str:
    return (
        f"✅ <b>Игрок сообщил об оплате!</b>\n\n"
        f"👤 Игрок: <b>{html.escape(nickname)}</b>\n"
        f"💰 Сумма: <b>{amount}₽</b>\n"
        f"📝 Memo: <code>{memo}</code>\n"
        f"🆔 Заявка №{order_id}\n\n"
        f"Проверьте оплату и откройте /admin для подтверждения."
    )


def _purchase_success_text(amount: int, currency: str) -> str:
    if currency == "coins":
        return (
            f"{E_CHECK_G} <b>Покупка успешна!</b>\n\n"
            f"{E_COINS} Зачислено: <b>{amount:,} монет</b>\n"
            f"Удачи в подземельях!"
        ).replace(",", ".")
    else:
        return (
            f"{E_CHECK_G} <b>Покупка успешна!</b>\n\n"
            f"{E_CRYSTALS} Зачислено: <b>{amount} кристаллов</b>\n"
            f"Удачи в подземельях!"
        )


# ============== OPEN DONATE FROM MARKET ==============

@router.message(F.text == "💸 Донат")
async def open_donate(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    balance = get_player_real_balance(user_id)
    await state.set_state(DonateMenu.viewing_coins)
    await message.answer(
        _donate_coins_text(balance),
        reply_markup=get_donate_coins_kb(),
        parse_mode="HTML"
    )


# ============== DONATE CALLBACKS ==============

@router.callback_query(F.data == "donate_tab:coins")
async def donate_switch_to_coins(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    player = get_player(user_id)
    if not player:
        await callback.answer("Сначала зарегистрируйся! /start", show_alert=True)
        return
    balance = get_player_real_balance(user_id)
    await state.set_state(DonateMenu.viewing_coins)
    await callback.message.edit_text(
        _donate_coins_text(balance),
        reply_markup=get_donate_coins_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "donate_tab:crystals")
async def donate_switch_to_crystals(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    player = get_player(user_id)
    if not player:
        await callback.answer("Сначала зарегистрируйся! /start", show_alert=True)
        return
    balance = get_player_real_balance(user_id)
    await state.set_state(DonateMenu.viewing_crystals)
    await callback.message.edit_text(
        _donate_crystals_text(balance),
        reply_markup=get_donate_crystals_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("donate_buy_coins:"))
async def donate_buy_coins(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    player = get_player(user_id)
    if not player:
        await callback.answer("Сначала зарегистрируйся! /start", show_alert=True)
        return
    parts = callback.data.split(":")
    coins = int(parts[1])
    price = int(parts[2])
    balance = get_player_real_balance(user_id)
    if balance < price:
        await callback.message.edit_text(
            _insufficient_funds_text(price, balance),
            reply_markup=get_donate_coins_kb(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    ok = deduct_real_balance(user_id, price)
    if not ok:
        await callback.answer("Недостаточно средств!", show_alert=True)
        return
    add_coins_to_player(user_id, coins)
    new_balance = get_player_real_balance(user_id)
    await callback.answer(f"✅ Куплено {coins:,} монет!".replace(",", "."), show_alert=True)
    await callback.message.edit_text(
        _donate_coins_text(new_balance),
        reply_markup=get_donate_coins_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("donate_buy_crystals:"))
async def donate_buy_crystals(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    player = get_player(user_id)
    if not player:
        await callback.answer("Сначала зарегистрируйся! /start", show_alert=True)
        return
    parts = callback.data.split(":")
    crystals = int(parts[1])
    price = int(parts[2])
    balance = get_player_real_balance(user_id)
    if balance < price:
        await callback.message.edit_text(
            _insufficient_funds_text(price, balance),
            reply_markup=get_donate_crystals_kb(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    ok = deduct_real_balance(user_id, price)
    if not ok:
        await callback.answer("Недостаточно средств!", show_alert=True)
        return
    add_crystals_to_player(user_id, crystals)
    new_balance = get_player_real_balance(user_id)
    await callback.answer(f"✅ Куплено {crystals} кристаллов!", show_alert=True)
    await callback.message.edit_text(
        _donate_crystals_text(new_balance),
        reply_markup=get_donate_crystals_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "donate_topup")
async def donate_topup_start(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    player = get_player(user_id)
    if not player:
        await callback.answer("Сначала зарегистрируйся! /start", show_alert=True)
        return
    await state.set_state(DonateMenu.entering_amount)
    await callback.answer()
    await callback.message.answer(
        f"{E_TAG}{E_GREEN2} <b>Укажите необходимую сумму для пополнения:</b>",
        parse_mode="HTML"
    )


@router.message(DonateMenu.entering_amount)
async def donate_enter_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    player = get_player(user_id)
    if not player:
        await message.answer("Сначала зарегистрируйся! /start")
        return
    text = message.text.strip()
    try:
        amount = int(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            f"{E_TAG}{E_GREEN2} <b>Укажите необходимую сумму для пополнения:</b>\n\n"
            f"{E_CROSS} Введите корректную сумму (целое число больше 0):",
            parse_mode="HTML"
        )
        return
    order = create_donation_order(user_id, player['nickname'], amount)
    order_id = order['order_id']
    memo = order['memo_code']
    await state.set_state(DonateMenu.waiting_payment)
    await state.update_data(current_order_id=order_id)
    await message.answer(
        _lot_created_text(amount, memo),
        reply_markup=get_payment_waiting_kb(order_id),
        parse_mode="HTML"
    )
    # Notify all admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=_admin_notify_new_order_text(player['nickname'], amount, memo, order_id),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Failed to notify admin {admin_id}: {e}")


@router.callback_query(F.data.startswith("donate_paid:"))
async def donate_paid_confirm(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    order = get_donation_order(order_id)
    if not order:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    if order['status'] == 'completed':
        await callback.answer("Эта заявка уже обработана!", show_alert=True)
        return
    update_donation_order_status(order_id, 'paid')
    await callback.answer("✅ Ваше уведомление об оплате отправлено администратору!")
    # Notify all admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=_admin_notify_paid_text(
                    order['nickname'], order['amount'], order['memo_code'], order_id
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Failed to notify admin {admin_id}: {e}")


@router.callback_query(F.data.startswith("donate_cancel:"))
async def donate_cancel_order(callback: types.CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    order = get_donation_order(order_id)
    if not order:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    if order['status'] == 'completed':
        await callback.answer("Эта заявка уже обработана!", show_alert=True)
        return
    update_donation_order_status(order_id, 'cancelled')
    await callback.answer("Заявка отменена.")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("❌ Заявка на пополнение отменена.")
    await state.clear()


# ============== ADMIN PAYMENT PANEL ==============

@router.message(Command("admin"))
async def open_admin_payment_panel(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    orders = get_pending_donation_orders()
    if not orders:
        await message.answer(
            "💼 <b>Панель оплат</b>\n\nЗаявок на пополнение нет.",
            reply_markup=get_admin_payment_kb([]),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"💼 <b>Панель оплат</b>\n\nАктивных заявок: {len(orders)}",
            reply_markup=get_admin_payment_kb(orders),
            parse_mode="HTML"
        )
    await state.set_state(AdminPaymentPanel.main_menu)


@router.callback_query(F.data == "adm_refresh")
async def admin_refresh_orders(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    orders = get_pending_donation_orders()
    text = (
        f"💼 <b>Панель оплат</b>\n\nАктивных заявок: {len(orders)}"
        if orders else
        "💼 <b>Панель оплат</b>\n\nЗаявок на пополнение нет."
    )
    try:
        await callback.message.edit_text(text, reply_markup=get_admin_payment_kb(orders), parse_mode="HTML")
    except Exception:
        pass
    await callback.answer("Обновлено!")


@router.callback_query(F.data.startswith("adm_order:"))
async def admin_view_order(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    order = get_donation_order(order_id)
    if not order:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    status_map = {'pending': '🟡 Ожидает оплаты', 'paid': '✅ Игрок оплатил', 'completed': '✔️ Завершена'}
    status_text = status_map.get(order['status'], order['status'])
    text = (
        f"📋 <b>Заявка №{order['order_id']}</b>\n\n"
        f"👤 Игрок: <b>{html.escape(order['nickname'])}</b>\n"
        f"💰 Сумма: <b>{order['amount']}₽</b>\n"
        f"📝 Memo: <code>{order['memo_code']}</code>\n"
        f"📊 Статус: {status_text}\n"
        f"🕐 Создана: {order['created_at']}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_order_action_kb(order_id),
        parse_mode="HTML"
    )
    await state.set_state(AdminPaymentPanel.viewing_order)
    await callback.answer()


@router.callback_query(F.data.startswith("adm_approve:"))
async def admin_approve_order(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    order = get_donation_order(order_id)
    if not order:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    if order['status'] == 'completed':
        await callback.answer("Заявка уже завершена!", show_alert=True)
        return
    add_real_balance(order['user_id'], order['amount'])
    update_donation_order_status(order_id, 'completed')
    await callback.answer(f"✅ Баланс пополнен на {order['amount']}₽!", show_alert=True)
    # Notify the player
    try:
        await bot.send_message(
            chat_id=order['user_id'],
            text=(
                f"✅ <b>Баланс пополнен!</b>\n\n"
                f"💰 Зачислено: <b>{order['amount']}₽</b>\n"
                f"Теперь вы можете купить игровую валюту в разделе <b>Рынок → Донат</b>!"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Failed to notify player {order['user_id']}: {e}")
    # Refresh admin view
    orders = get_pending_donation_orders()
    text = (
        f"💼 <b>Панель оплат</b>\n\nАктивных заявок: {len(orders)}"
        if orders else
        "💼 <b>Панель оплат</b>\n\nЗаявок на пополнение нет."
    )
    await callback.message.edit_text(text, reply_markup=get_admin_payment_kb(orders), parse_mode="HTML")
    await state.set_state(AdminPaymentPanel.main_menu)


@router.callback_query(F.data.startswith("adm_reject:"))
async def admin_reject_order(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    order_id = int(callback.data.split(":")[1])
    order = get_donation_order(order_id)
    if not order:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    if order['status'] == 'completed':
        await callback.answer("Заявка уже завершена!", show_alert=True)
        return
    update_donation_order_status(order_id, 'completed')
    await callback.answer("Заявка отклонена.")
    # Notify the player
    try:
        await bot.send_message(
            chat_id=order['user_id'],
            text=(
                f"❌ <b>Заявка на пополнение отклонена.</b>\n\n"
                f"💰 Сумма: {order['amount']}₽\n"
                f"Если вы уже оплатили — свяжитесь с администратором."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Failed to notify player {order['user_id']}: {e}")
    # Refresh admin view
    orders = get_pending_donation_orders()
    text = (
        f"💼 <b>Панель оплат</b>\n\nАктивных заявок: {len(orders)}"
        if orders else
        "💼 <b>Панель оплат</b>\n\nЗаявок на пополнение нет."
    )
    await callback.message.edit_text(text, reply_markup=get_admin_payment_kb(orders), parse_mode="HTML")
    await state.set_state(AdminPaymentPanel.main_menu)

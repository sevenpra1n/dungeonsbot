"""Moderator panel handler: warnings, bans, and ban appeals."""

import html
import logging

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.loader import bot
from bot.config import ADMIN_IDS
from bot.states import ModeratorPanel, BanAppealState
from bot.database import (
    get_player, get_player_by_nickname,
    get_player_warnings, give_warning, remove_warning, reset_warnings,
    get_player_ban, is_player_banned, ban_player, unban_player,
    format_ban_remaining, get_ban_remaining_seconds,
    create_ban_appeal, get_ban_appeal, get_pending_appeals, update_appeal_status,
)
from bot.keyboards import (
    get_moderator_main_kb, get_mod_appeals_list_kb, get_mod_appeal_action_kb,
    get_warn_ack_kb, get_ban_appeal_kb,
)

router = Router()
logger = logging.getLogger(__name__)

# ─── Custom emoji shortcuts ────────────────────────────────────────────────
_E_RED      = '<tg-emoji emoji-id="5907027122446145395">🔴</tg-emoji>'
_E_YELLOW   = '<tg-emoji emoji-id="5906800644525660990">🟡</tg-emoji>'
_E_WARN     = '<tg-emoji emoji-id="5276240711795107620">⚠️</tg-emoji>'
_E_MEGA     = '<tg-emoji emoji-id="5278528159837348960">📢</tg-emoji>'
_E_CAL      = '<tg-emoji emoji-id="5472279086657199080">🗓️</tg-emoji>'
_E_MARKER   = '<tg-emoji emoji-id="5267324424113124134">▫️</tg-emoji>'
_E_UNLOCK   = '<tg-emoji emoji-id="5429405838345265327">🔓</tg-emoji>'
_E_HOUR     = '<tg-emoji emoji-id="5287579571485422439">⏳</tg-emoji>'
_E_CLOCK    = '<tg-emoji emoji-id="5276412364458059956">🕓</tg-emoji>'
_MAX_WARNINGS = 3
_AUTO_BAN_SECONDS = 30 * 60  # 30 minutes


def _warn_text(nickname: str, reason: str, count: int) -> str:
    return (
        f"{_E_RED}{_E_WARN} {html.escape(nickname)}, вам было выдано предупреждение!\n\n"
        f"{_E_MARKER}{_E_MEGA} Причина: {html.escape(reason)}\n"
        f"{_E_MARKER}{_E_RED}{_E_CAL} Предупреждение: {count} / {_MAX_WARNINGS}"
    )


def _ban_text(nickname: str, reason: str, remaining: str) -> str:
    return (
        f"{_E_RED}{_E_UNLOCK} {html.escape(nickname)}, вы получили бан!\n"
        f"{_E_RED}Вам запрещены любые действия в боте.\n\n"
        f"{_E_MARKER}{_E_MEGA} Причина: {html.escape(reason)}\n"
        f"{_E_MARKER}{_E_RED}{_E_HOUR} Оставшееся время: {html.escape(remaining)} {_E_CLOCK}"
    )


def _ban_active_text(nickname: str, reason: str, remaining: str) -> str:
    return (
        f"{_E_YELLOW}{_E_UNLOCK} {html.escape(nickname)}, ожидайте разблокировки бана!\n"
        f"{_E_RED}Вам запрещены любые действия в боте.\n\n"
        f"{_E_MARKER}{_E_MEGA} Причина: {html.escape(reason)}\n"
        f"{_E_MARKER}{_E_RED}{_E_HOUR} Оставшееся время: {html.escape(remaining)} {_E_CLOCK}"
    )


def _appeal_prompt_text() -> str:
    return (
        f"{_E_MARKER}{_E_MEGA} У вас есть возможность обжаловать блокировку!\n"
        "(Напишите ниже причину для разблокировки)."
    )


# ─── /moderator command ────────────────────────────────────────────────────

@router.message(Command("moderator"))
async def open_moderator(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(ModeratorPanel.main_menu)
    await message.answer(
        "🛡️ <b>Панель модератора</b>\n\nВыберите действие:",
        reply_markup=get_moderator_main_kb(),
        parse_mode="HTML"
    )


# ─── Moderator main menu callbacks ────────────────────────────────────────

@router.callback_query(F.data == "mod_main")
async def mod_main_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await state.set_state(ModeratorPanel.main_menu)
    await callback.message.edit_text(
        "🛡️ <b>Панель модератора</b>\n\nВыберите действие:",
        reply_markup=get_moderator_main_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "mod_warn")
async def mod_warn_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await state.set_state(ModeratorPanel.entering_nickname_warn)
    await callback.message.edit_text(
        "⚠️ <b>Выдача предупреждения</b>\n\nВведите никнейм игрока:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "mod_ban")
async def mod_ban_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await state.set_state(ModeratorPanel.entering_nickname_ban)
    await callback.message.edit_text(
        "🔴 <b>Выдача бана</b>\n\nВведите никнейм игрока:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "mod_unwarn")
async def mod_unwarn_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await state.set_state(ModeratorPanel.entering_nickname_unwarn)
    await callback.message.edit_text(
        "✅ <b>Снятие предупреждения</b>\n\nВведите никнейм игрока:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "mod_unban")
async def mod_unban_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await state.set_state(ModeratorPanel.entering_nickname_unban)
    await callback.message.edit_text(
        "🟢 <b>Снятие бана</b>\n\nВведите никнейм игрока:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "mod_check")
async def mod_check_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await state.set_state(ModeratorPanel.entering_nickname_warn)
    await callback.message.edit_text(
        "🔍 <b>Проверка игрока</b>\n\nВведите никнейм игрока:",
        parse_mode="HTML"
    )
    await state.update_data(mod_action="check")
    await callback.answer()


@router.callback_query(F.data == "mod_appeals")
async def mod_appeals_list(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    appeals = get_pending_appeals()
    await state.set_state(ModeratorPanel.viewing_appeals)
    if not appeals:
        await callback.message.edit_text(
            "📋 <b>Заявки на разблокировку</b>\n\nЗаявок нет.",
            reply_markup=get_mod_appeals_list_kb([]),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"📋 <b>Заявки на разблокировку</b>\n\nОжидает: {len(appeals)}",
            reply_markup=get_mod_appeals_list_kb(appeals),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("mod_appeal_view:"))
async def mod_appeal_view(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    appeal_id = int(callback.data.split(":")[1])
    appeal = get_ban_appeal(appeal_id)
    if not appeal:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    player = get_player(appeal['user_id'])
    nick = html.escape(player['nickname']) if player else "?"
    await state.set_state(ModeratorPanel.viewing_appeal)
    await callback.message.edit_text(
        f"📋 <b>Заявка #{appeal_id}</b>\n\n"
        f"👤 Игрок: {nick}\n"
        f"📝 Текст:\n{html.escape(appeal['appeal_text'])}\n\n"
        f"📅 Дата: {appeal['created_at']}",
        reply_markup=get_mod_appeal_action_kb(appeal_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mod_appeal_accept:"))
async def mod_appeal_accept(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    appeal_id = int(callback.data.split(":")[1])
    appeal = get_ban_appeal(appeal_id)
    if not appeal:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    unban_player(appeal['user_id'])
    reset_warnings(appeal['user_id'])
    update_appeal_status(appeal_id, "accepted")
    player = get_player(appeal['user_id'])
    nick = player['nickname'] if player else "?"
    # Notify player
    try:
        await bot.send_message(
            chat_id=appeal['user_id'],
            text=(
                f"✅ <b>Вы были разблокированы!</b>\n\n"
                f"Ваша заявка одобрена. Добро пожаловать обратно!\n"
                f"Пожалуйста, больше не нарушайте правила Hades."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Failed to notify player {appeal['user_id']}: {e}")
    await callback.message.edit_text(
        f"✅ Игрок {html.escape(nick)} разблокирован.",
        parse_mode="HTML"
    )
    await callback.answer("Игрок разблокирован.")


@router.callback_query(F.data.startswith("mod_appeal_reject:"))
async def mod_appeal_reject(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    appeal_id = int(callback.data.split(":")[1])
    appeal = get_ban_appeal(appeal_id)
    if not appeal:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    update_appeal_status(appeal_id, "rejected")
    player = get_player(appeal['user_id'])
    nick = player['nickname'] if player else "?"
    # Notify player
    try:
        ban = get_player_ban(appeal['user_id'])
        remaining = format_ban_remaining(appeal['user_id']) if ban else "—"
        await bot.send_message(
            chat_id=appeal['user_id'],
            text=(
                f"❌ Ваша заявка на разблокировку отклонена.\n\n"
                f"Оставшееся время бана: {remaining}"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Failed to notify player {appeal['user_id']}: {e}")
    await callback.message.edit_text(
        f"❌ Заявка игрока {html.escape(nick)} отклонена.",
        parse_mode="HTML"
    )
    await callback.answer("Заявка отклонена.")


# ─── Moderator FSM message handlers ────────────────────────────────────────

@router.message(ModeratorPanel.entering_nickname_warn)
async def mod_entering_nickname_warn(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    data = await state.get_data()
    action = data.get("mod_action", "warn")

    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"❌ Игрок «{html.escape(nickname)}» не найден.", parse_mode="HTML")
        return

    if action == "check":
        warnings = get_player_warnings(target['user_id'])
        ban = get_player_ban(target['user_id'])
        ban_status = "нет"
        if ban and is_player_banned(target['user_id']):
            remaining = format_ban_remaining(target['user_id'])
            ban_status = f"Заблокирован (осталось {remaining})"
        await message.answer(
            f"🔍 <b>Игрок: {html.escape(nickname)}</b>\n\n"
            f"⚠️ Предупреждения: {warnings['count']} / {_MAX_WARNINGS}\n"
            f"Причина последнего: {html.escape(warnings['last_reason'] or '—')}\n\n"
            f"🔴 Бан: {ban_status}",
            reply_markup=get_moderator_main_kb(),
            parse_mode="HTML"
        )
        await state.update_data(mod_action=None)
        await state.set_state(ModeratorPanel.main_menu)
        return

    await state.update_data(warn_target_id=target['user_id'], warn_target_nick=nickname)
    await state.set_state(ModeratorPanel.entering_reason_warn)
    await message.answer(
        f"⚠️ Игрок найден: <b>{html.escape(nickname)}</b>\n\nВведите причину предупреждения:",
        parse_mode="HTML"
    )


@router.message(ModeratorPanel.entering_reason_warn)
async def mod_entering_reason_warn(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    reason = message.text.strip()
    data = await state.get_data()
    target_id = data.get("warn_target_id")
    target_nick = data.get("warn_target_nick", "?")

    new_count = give_warning(target_id, reason)
    await state.set_state(ModeratorPanel.main_menu)

    if new_count >= _MAX_WARNINGS:
        # Auto-ban for 30 minutes
        ban_player(target_id, reason, _AUTO_BAN_SECONDS, banned_by=message.from_user.id)
        reset_warnings(target_id)
        remaining = format_ban_remaining(target_id)
        ban_msg = _ban_text(target_nick, reason, remaining)
        try:
            await bot.send_message(
                chat_id=target_id,
                text=ban_msg,
                reply_markup=get_ban_appeal_kb(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Failed to notify player {target_id}: {e}")
        await message.answer(
            f"✅ Игрок <b>{html.escape(target_nick)}</b> получил 3-е предупреждение и автоматически заблокирован на 30 минут.",
            reply_markup=get_moderator_main_kb(),
            parse_mode="HTML"
        )
    else:
        warn_msg = _warn_text(target_nick, reason, new_count)
        try:
            await bot.send_message(
                chat_id=target_id,
                text=warn_msg,
                reply_markup=get_warn_ack_kb(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Failed to notify player {target_id}: {e}")
        await message.answer(
            f"✅ Предупреждение выдано игроку <b>{html.escape(target_nick)}</b>. "
            f"Итого: {new_count}/{_MAX_WARNINGS}",
            reply_markup=get_moderator_main_kb(),
            parse_mode="HTML"
        )


@router.message(ModeratorPanel.entering_nickname_ban)
async def mod_entering_nickname_ban(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"❌ Игрок «{html.escape(nickname)}» не найден.", parse_mode="HTML")
        return
    await state.update_data(ban_target_id=target['user_id'], ban_target_nick=nickname)
    await state.set_state(ModeratorPanel.entering_reason_ban)
    await message.answer(
        f"🔴 Игрок найден: <b>{html.escape(nickname)}</b>\n\nВведите причину бана:",
        parse_mode="HTML"
    )


@router.message(ModeratorPanel.entering_reason_ban)
async def mod_entering_reason_ban(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    reason = message.text.strip()
    await state.update_data(ban_reason=reason)
    await state.set_state(ModeratorPanel.entering_duration_ban)
    await message.answer(
        f"⏳ Причина: <b>{html.escape(reason)}</b>\n\nВведите длительность бана в секундах:",
        parse_mode="HTML"
    )


@router.message(ModeratorPanel.entering_duration_ban)
async def mod_entering_duration_ban(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        duration = int(message.text.strip())
        if duration <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите число больше нуля (секунды).")
        return

    data = await state.get_data()
    target_id = data.get("ban_target_id")
    target_nick = data.get("ban_target_nick", "?")
    reason = data.get("ban_reason", "—")

    ban_player(target_id, reason, duration, banned_by=message.from_user.id)
    remaining = format_ban_remaining(target_id)
    ban_msg = _ban_text(target_nick, reason, remaining)
    try:
        await bot.send_message(
            chat_id=target_id,
            text=ban_msg,
            reply_markup=get_ban_appeal_kb(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Failed to notify player {target_id}: {e}")

    await state.set_state(ModeratorPanel.main_menu)
    await message.answer(
        f"✅ Игрок <b>{html.escape(target_nick)}</b> заблокирован на {duration} секунд.",
        reply_markup=get_moderator_main_kb(),
        parse_mode="HTML"
    )


@router.message(ModeratorPanel.entering_nickname_unwarn)
async def mod_entering_nickname_unwarn(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"❌ Игрок «{html.escape(nickname)}» не найден.", parse_mode="HTML")
        return

    new_count = remove_warning(target['user_id'])
    await state.set_state(ModeratorPanel.main_menu)

    try:
        await bot.send_message(
            chat_id=target['user_id'],
            text=(
                f"✅ С вас снято одно предупреждение!\n"
                f"Текущее количество предупреждений: {new_count}/{_MAX_WARNINGS}"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Failed to notify player {target['user_id']}: {e}")

    await message.answer(
        f"✅ Предупреждение снято с игрока <b>{html.escape(nickname)}</b>. "
        f"Осталось: {new_count}/{_MAX_WARNINGS}",
        reply_markup=get_moderator_main_kb(),
        parse_mode="HTML"
    )


@router.message(ModeratorPanel.entering_nickname_unban)
async def mod_entering_nickname_unban(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    nickname = message.text.strip()
    target = get_player_by_nickname(nickname)
    if not target:
        await message.answer(f"❌ Игрок «{html.escape(nickname)}» не найден.", parse_mode="HTML")
        return

    if not is_player_banned(target['user_id']):
        await message.answer(
            f"ℹ️ Игрок <b>{html.escape(nickname)}</b> не заблокирован.",
            reply_markup=get_moderator_main_kb(),
            parse_mode="HTML"
        )
        await state.set_state(ModeratorPanel.main_menu)
        return

    unban_player(target['user_id'])
    await state.set_state(ModeratorPanel.main_menu)

    try:
        await bot.send_message(
            chat_id=target['user_id'],
            text="🟢 Ваш бан был снят модератором. Добро пожаловать обратно!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Failed to notify player {target['user_id']}: {e}")

    await message.answer(
        f"✅ Бан снят с игрока <b>{html.escape(nickname)}</b>.",
        reply_markup=get_moderator_main_kb(),
        parse_mode="HTML"
    )


# ─── Player-side callbacks ─────────────────────────────────────────────────

@router.callback_query(F.data == "warn_ack")
async def warn_acknowledge(callback: types.CallbackQuery, state: FSMContext):
    """Игрок нажал 'Извиняюсь' — удалить сообщение с предупреждением"""
    await callback.message.delete()
    await callback.answer("Принято!")


@router.callback_query(F.data == "appeal_ban")
async def appeal_ban_start(callback: types.CallbackQuery, state: FSMContext):
    """Игрок хочет обжаловать блокировку"""
    user_id = callback.from_user.id
    if not is_player_banned(user_id):
        await callback.answer("Вы не заблокированы.", show_alert=True)
        return
    await state.set_state(BanAppealState.writing_appeal)
    await callback.message.answer(
        _appeal_prompt_text(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(BanAppealState.writing_appeal)
async def handle_appeal_text(message: types.Message, state: FSMContext):
    """Игрок написал текст апелляции"""
    user_id = message.from_user.id
    if not is_player_banned(user_id):
        await state.clear()
        await message.answer("Вы не заблокированы.")
        return
    player = get_player(user_id)
    if not player:
        await state.clear()
        return

    appeal_text = message.text.strip()
    if not appeal_text:
        await message.answer("Пожалуйста, напишите причину для разблокировки.")
        return

    appeal_id = create_ban_appeal(user_id, appeal_text)
    await state.clear()

    await message.answer(
        "✅ Ваша заявка принята и передана модерации на рассмотрение.\n"
        "Ожидайте ответа.",
        parse_mode="HTML"
    )

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"📋 <b>Новая заявка на разблокировку #{appeal_id}</b>\n\n"
                    f"👤 Игрок: {html.escape(player['nickname'])}\n"
                    f"📝 Причина:\n{html.escape(appeal_text)}\n\n"
                    f"Используйте /moderator → Заявки на разблокировку"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Failed to notify admin {admin_id}: {e}")


# ─── Ban check middleware helper ───────────────────────────────────────────

async def check_and_block_banned(user_id: int, send_func) -> bool:
    """
    Проверить бан игрока. Если забанен — отправить сообщение о бане и вернуть True.
    send_func — async callable(text, reply_markup, parse_mode).
    """
    if not is_player_banned(user_id):
        return False
    player = get_player(user_id)
    if not player:
        return False
    ban = get_player_ban(user_id)
    if not ban:
        return False
    remaining = format_ban_remaining(user_id)
    await send_func(
        _ban_active_text(player['nickname'], ban['reason'], remaining),
        get_ban_appeal_kb(),
        "HTML"
    )
    return True

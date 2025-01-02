from aiogram.types import Message, CallbackQuery
from aiogram import Dispatcher, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from finance.check_withdrawable_stars import get_withdrawable_stars
from finance.withdraw import check_withdrawable_stars, process_withdrawal
from keyboards.keyboard import cancel_keyboard
from localisation.check_language import check_language
from localisation.translations import translations

router = Router()

class WithdrawalState(StatesGroup):
    waiting_for_amount = State()

async def withdraw_handler(message: Message, dp: Dispatcher, user_language: str, state: FSMContext):
    """
    Хендлер для обработки кнопки "Вывести".
    """
    pool = dp["db_pool"]
    user_id = message.from_user.id

    stars_available = await check_withdrawable_stars(pool, user_id)
    available_stars = await get_withdrawable_stars(pool, user_id)
    if not stars_available:
        await message.reply(
            translations["withdraw_unavailable"][user_language].format(available_stars=available_stars)
        )
        return

    sent_message = await message.reply(
        translations["withdraw_available"][user_language].format(available_stars=available_stars) +
        translations["withdraw"][user_language],
        reply_markup=cancel_keyboard(user_language)
    )

    await state.set_state(WithdrawalState.waiting_for_amount)
    await state.update_data(
        available_stars=available_stars,
        db_pool=dp["db_pool"],
        message_ids=[message.message_id, sent_message.message_id]
    )

@router.message(WithdrawalState.waiting_for_amount)
async def process_withdrawal_input(message: Message, state: FSMContext):
    """
    Обработка ввода суммы для вывода.
    """
    data = await state.get_data()
    available_stars = data.get("available_stars")
    db_pool = data.get("db_pool")
    message_ids = data.get("message_ids", [])

    if not db_pool:
        await message.answer("Ошибка: подключение к базе данных не найдено.")
        return

    user_id = message.from_user.id
    user_language = await check_language(db_pool, user_id)

    if not message.text.isdigit():
        error_message = await message.reply(translations["invalid_amount"][user_language])
        message_ids.append(error_message.message_id)
        await state.update_data(message_ids=message_ids)
        return

    amount_to_withdraw = int(message.text)

    if amount_to_withdraw < 1000:
        error_message = await message.reply(translations["min_withdraw"][user_language])
        message_ids.append(error_message.message_id)
        await state.update_data(message_ids=message_ids)
        return

    if amount_to_withdraw > available_stars:
        error_message = await message.reply(
            translations["max_withdraw"][user_language].format(available_stars=available_stars)
        )
        message_ids.append(error_message.message_id)
        await state.update_data(message_ids=message_ids)
        return

    result_message = await process_withdrawal(db_pool, user_id, amount_to_withdraw, user_language)
    sent_message = await message.answer(result_message)

    message_ids.append(message.message_id)
    await delete_all_messages_except_last(message.bot, message.chat.id, message_ids, sent_message.message_id)

    await state.clear()

@router.callback_query(lambda callback: callback.data == "cancel_withdraw")
async def cancel_withdraw(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработка кнопки "Отмена" — удаляет все сообщения.
    """
    data = await state.get_data()
    message_ids = data.get("message_ids", [])

    await delete_all_messages(callback_query.bot, callback_query.message.chat.id, message_ids)

    await state.clear()

async def delete_all_messages_except_last(bot, chat_id, message_ids, last_message_id):
    """
    Удаляет все сообщения, кроме последнего сообщения с успешным результатом.
    """
    for message_id in message_ids:
        if message_id != last_message_id:
            try:
                await bot.delete_message(chat_id, message_id)
            except Exception:
                pass

async def delete_all_messages(bot, chat_id, message_ids):
    """
    Удаляет все сообщения по их ID.
    """
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception:
            pass 
from aiogram import Router
from aiogram.types import Message
from aiogram import Dispatcher
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
        await message.answer(
            translations["withdraw_unavailable"][user_language].format(available_stars=available_stars)
        )
        return

    await message.answer(
        translations["withdraw_available"][user_language].format(available_stars=available_stars) +
        translations["withdraw"][user_language],
        reply_markup=cancel_keyboard(user_language)
    )

    await state.set_state(WithdrawalState.waiting_for_amount)
    await state.update_data(
        available_stars=available_stars,
        db_pool=pool
    )


@router.message(WithdrawalState.waiting_for_amount)
async def process_withdrawal_input(message: Message, state: FSMContext):
    """
    Ожидание ввода суммы для вывода.
    """
    data = await state.get_data()
    available_stars = data.get("available_stars")
    db_pool = data.get("db_pool")

    if not db_pool:
        await message.answer("Ошибка: подключение к базе данных не найдено.")
        return

    user_id = message.from_user.id

    user_language = await check_language(db_pool, user_id)

    if not message.text.isdigit():
        await message.answer(translations["invalid_amount"][user_language])
        return

    amount_to_withdraw = int(message.text)

    if amount_to_withdraw < 1000:
        await message.answer(translations["min_withdraw"][user_language])
        return

    if amount_to_withdraw > available_stars:
        await message.answer(
            translations["max_withdraw"][user_language].format(available_stars=available_stars)
        )
        return

    result_message = await process_withdrawal(db_pool, user_id, amount_to_withdraw, user_language)
    await message.answer(result_message)

    await state.clear()

@router.callback_query(lambda callback: callback.data == "cancel_withdraw")
async def cancel_withdraw(callback_query, state: FSMContext):
    """
    Обработка кнопки "Отмена".
    """
    await state.clear()

    await callback_query.message.delete()

    try:
        await callback_query.bot.delete_message(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id - 1
        )
    except Exception:
        pass
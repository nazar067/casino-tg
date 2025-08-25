from aiogram.types import Message, CallbackQuery
from aiogram import Dispatcher, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from finance.check_withdrawable_stars import get_withdrawable_stars
from finance.withdraw import process_withdrawal
from games.dice.check_active_game import has_active_game
from keyboards.keyboard import withdraw_keyboard
from localisation.get_language import get_language
from localisation.translations.finance import translations as finance_translation

router = Router()

class WithdrawalState(StatesGroup):
    waiting_for_amount = State()

async def withdraw_handler(message: Message, dp: Dispatcher, user_language: str):
    """
    Хендлер для обработки кнопки "Вывести".
    """
    if message.chat.type != "private":
        await message.reply(finance_translation["withdraw_private_chat_error"][user_language])
        return
    
    pool = dp["db_pool"]
    user_id = message.from_user.id
    
    if await has_active_game(pool, user_id):
        await message.reply(finance_translation["withdraw_active_game_error"][user_language])
        return

    available_stars = await get_withdrawable_stars(pool, user_id)
    if available_stars <= 0:
        await message.reply(finance_translation["withdraw_unavailable"][user_language])
        return

    await message.reply(
        text=finance_translation["withdraw_text"][user_language],
        reply_markup=withdraw_keyboard(user_language)
    )

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
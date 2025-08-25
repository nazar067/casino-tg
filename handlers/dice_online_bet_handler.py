from aiogram.types import Message, CallbackQuery
from aiogram import Dispatcher, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from games.dice.check_active_game import has_active_game
from games.dice.search_online_dice import search_dice
from keyboards.keyboard import cancel_withdraw_keyboard
from localisation.get_language import get_language
from localisation.translations.finance import translations as finance_translation
from user.balance import get_user_balance
from localisation.translations.dice import translations as dice_translation

router = Router()
    
class SearchDiceStates(StatesGroup):
    waiting_for_min_bet = State()
    waiting_for_max_bet = State()

async def search_dice_handler(message: Message, dp: Dispatcher, user_language: str, state: FSMContext):
    """
    Хендлер для начала поиска игры в кости.
    """
    pool = dp["db_pool"]
    user_id = message.from_user.id
    if message.chat.type != "private":
        await message.reply(finance_translation["withdraw_private_chat_error"][user_language])
        return

    if await has_active_game(pool, user_id):
        await message.reply(dice_translation["error_already_in_game_msg"][user_language])
        return

    user_balance = await get_user_balance(pool, user_id)
    recomend_min_bet, recomend_max_bet = await recomend_bet(pool) 
    sent_message = await message.reply(
        dice_translation["enter_min_bet_msg"][user_language].format(recomend_min_bet=recomend_min_bet, recomend_max_bet=recomend_max_bet).replace(".", "\\."),
        reply_markup=cancel_withdraw_keyboard(user_language),
        parse_mode="MarkdownV2"
    )

    await state.set_state(SearchDiceStates.waiting_for_min_bet)
    await state.update_data(
        user_balance=user_balance,
        db_pool=pool,
        message_ids=[message.message_id, sent_message.message_id]
    )

@router.message(SearchDiceStates.waiting_for_min_bet)
async def get_min_bet(message: Message, state: FSMContext):
    """
    Обработка минимальной ставки.
    """
    data = await state.get_data()
    pool = data.get("db_pool")
    user_language = await get_language(pool, message.chat.id)
    user_balance = data.get("user_balance")
    message_ids = data.get("message_ids", [])

    if not message.text.isdigit():
        error_message = await message.reply(dice_translation["invalid_bet_msg"][user_language])
        message_ids.append(error_message.message_id)
        await state.update_data(message_ids=message_ids)
        return

    min_bet = int(message.text)
    
    if min_bet < 1:
        error_message = await message.reply(dice_translation["lowest_min_bet_msg"][user_language])
        message_ids.append(error_message.message_id)
        await state.update_data(message_ids=message_ids)
        return 

    if min_bet > user_balance:
        error_message = await message.reply(dice_translation["min_bet_exceeds_balance_msg"][user_language])
        message_ids.append(error_message.message_id)
        await state.update_data(message_ids=message_ids)
        return

    for msg_id in message_ids:
        try:
            await message.bot.delete_message(message.chat.id, msg_id)
        except Exception:
            pass

    recomend_min_bet, recomend_max_bet = await recomend_bet(pool) 
    sent_message = await message.reply(
        dice_translation["enter_max_bet_msg"][user_language].format(recomend_min_bet=recomend_min_bet, recomend_max_bet=recomend_max_bet).replace(".", "\\."),
        reply_markup=cancel_withdraw_keyboard(user_language),
        parse_mode="MarkdownV2"
        )
    await state.update_data(
        min_bet=min_bet,
        message_ids=[message.message_id, sent_message.message_id]
    )
    await state.set_state(SearchDiceStates.waiting_for_max_bet)

@router.message(SearchDiceStates.waiting_for_max_bet)
async def get_max_bet(message: Message, state: FSMContext):
    """
    Обработка максимальной ставки.
    """
    data = await state.get_data()
    pool = data.get("db_pool")
    user_language = await get_language(pool, message.chat.id)
    min_bet = data.get("min_bet")
    user_balance = data.get("user_balance")
    message_ids = data.get("message_ids", [])

    if not message.text.isdigit():
        error_message = await message.reply(dice_translation["invalid_bet_msg"][user_language])
        message_ids.append(error_message.message_id)
        await state.update_data(message_ids=message_ids)
        return

    max_bet = int(message.text)

    if max_bet > user_balance:
        error_message = await message.reply(dice_translation["max_bet_exceeds_balance_msg"][user_language])
        message_ids.append(error_message.message_id)
        await state.update_data(message_ids=message_ids)
        return

    if max_bet < min_bet:
        error_message = await message.reply(dice_translation["max_bet_less_than_min_bet_msg"][user_language])
        message_ids.append(error_message.message_id)
        await state.update_data(message_ids=message_ids)
        return

    # Удаляем сообщения предыдущего этапа
    for msg_id in message_ids + [message.message_id]:
        try:
            await message.bot.delete_message(message.chat.id, msg_id)
        except Exception:
            pass

    await search_dice(pool, message, min_bet=min_bet, max_bet=max_bet)

    await state.clear()

@router.callback_query(lambda callback: callback.data == "cancel_dice_online")
async def cancel_dice_search(callback_query: CallbackQuery, state: FSMContext):
    """
    Отмена поиска игры.
    """
    data = await state.get_data()
    message_ids = data.get("message_ids", [])

    await delete_all_messages(callback_query.bot, callback_query.message.chat.id, message_ids)
    await state.clear()

async def delete_all_messages(bot, chat_id, message_ids):
    """
    Удаляет все сообщения по их ID.
    """
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        
async def recomend_bet(pool):
    """
    Ищет игру с минимальной ставкой среди активных онлайн-игр и рекомендует диапазон ставок.
    """
    async with pool.acquire() as connection:
        game = await connection.fetchrow("""
            SELECT bet FROM game_dice
            WHERE is_closed = FALSE AND online = TRUE
            ORDER BY bet ASC
            LIMIT 1
        """)

        if game:
            bet = game["bet"]
            recomend_min_bet = bet
            recomend_max_bet = bet + 20
            return recomend_min_bet, recomend_max_bet
        return 50, 100

    
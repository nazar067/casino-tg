from aiogram.types import Message
from aiogram import Dispatcher, Router

from games.dice.check_active_game import has_active_game
from localisation.translations.dice import translations as dice_translation
from localisation.get_language import get_language
from user.balance import get_user_balance
from keyboards.keyboard import game_buttons, online_game_buttons

router = Router()

async def create_game_handler(message: Message, pool, state, online=False):
    """
    Создание новой игры в кости (offline или online).
    """
    user_id = message.from_user.id
    user_language = await get_language(pool, message.chat.id)

    if await has_active_game(pool, user_id):
        await message.reply(dice_translation["error_already_in_game_msg"][user_language])
        return

    try:
        bet = int(message.text.split(maxsplit=1)[1])
        if bet <= 0:
            raise ValueError
    except (IndexError, ValueError):
        await message.answer(dice_translation["register_help_msg"][user_language])
        return
    
    user_balance = await get_user_balance(pool, user_id)
    if user_balance < bet:
        await message.answer(dice_translation["register_no_stars_msg"][user_language])
        return

    async with pool.acquire() as connection:
        game_message = await message.answer(
            dice_translation["wait_second_player_msg"][user_language].format(game_id="...", bet=bet),
            reply_markup=online_game_buttons("...", bet, user_language)
            if online
            else game_buttons("...", bet, user_language)
        )
        game_message_id = game_message.message_id

        game_id = await connection.fetchval("""
            INSERT INTO game_dice (chat_id, start_msg_id, player1_id, bet, is_closed, online)
            VALUES ($1, $2, $3, $4, FALSE, $5)
            RETURNING id
        """, message.chat.id, game_message_id, user_id, bet, online)

        await game_message.edit_text(
            dice_translation["wait_second_player_msg"][user_language].format(game_id=game_id, bet=bet),
            reply_markup=online_game_buttons(game_id, bet, user_language)
            if online
            else game_buttons(game_id, bet, user_language)
        )

    await state.update_data(
        creator_message_id=message.message_id,
        game_message_id=game_message_id,
        game_id=game_id
    )

def setup_register_game_handlers(dp: Dispatcher):
    dp.include_router(router)

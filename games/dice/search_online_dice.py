from math import ceil
from aiogram.types import CallbackQuery, Message
import logging

from games.dice.check_active_game import has_active_game
from games.dice.join_game import join_game_handler
from keyboards.keyboard import online_game_buttons
from localisation.get_language import get_language
from user.balance import get_user_balance
from localisation.translations.dice import translations as dice_translation

async def search_dice(pool, message, min_bet: int, max_bet: int):
    """
    Ищет доступные онлайн игры и автоматически присоединяет второго игрока.
    Если подходящей игры нет, создаёт новую.

    :param pool: Пул соединений с базой данных.
    :param bot: Экземпляр бота.
    :param message: Объект сообщения от пользователя.
    :param min_bet: Минимальная ставка для поиска игр.
    :param max_bet: Максимальная ставка для поиска игр.
    """
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_language = await get_language(pool, chat_id)

        async with pool.acquire() as connection:
            game = await connection.fetchrow("""
                SELECT id, player1_id, bet
                FROM game_dice
                WHERE is_closed = FALSE
                  AND online = TRUE
                  AND player1_id IS NOT NULL
                  AND player2_id IS NULL
                  AND bet >= $1
                  AND bet <= $2
                LIMIT 1
            """, min_bet, max_bet)

            if game:
                game_id = game["id"]
                fake_callback = CallbackQuery(
                    id="search_dice_callback",
                    from_user=message.from_user,
                    message=message,
                    chat_instance="fake_instance",
                    data=f"join_game:{game_id}"
                )
                await join_game_handler(fake_callback, pool, online=True)
                return

            bet = ceil((min_bet + max_bet) / 2)

            if await has_active_game(pool, user_id):
                await message.reply(dice_translation["error_already_in_game_msg"][user_language])
                return

            user_balance = await get_user_balance(pool, user_id)
            if user_balance < bet:
                await message.reply(dice_translation["register_no_stars_msg"][user_language])
                return
            game_message = await message.answer(
                dice_translation["searching_online"][user_language].format(bet=bet), reply_markup=online_game_buttons("...", bet, user_language)
            )
            game_message_id = game_message.message_id

            game_id = await connection.fetchval("""
                INSERT INTO game_dice (chat_id, start_msg_id, player1_id, bet, is_closed, online)
                VALUES ($1, $2, $3, $4, FALSE, TRUE)
                RETURNING id
            """, chat_id, game_message_id, user_id, bet)
            await game_message.edit_text(
                dice_translation["searching_online"][user_language].format(bet=bet), reply_markup=online_game_buttons(game_id, bet, user_language)
            )

    except Exception as e:
        logging.error(f"Error in search_dice: {e}", exc_info=True)
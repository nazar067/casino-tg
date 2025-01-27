from datetime import datetime
import logging
from aiogram.types import Message
from aiogram import Router
import asyncio
from finance.account import account_addition, account_withdrawal
from games.dice.game_result import process_game_result
from localisation.get_language import get_language
from localisation.translations.dice import translations as dice_translation

router = Router()

async def handle_dice_roll(pool, message: Message):
    """
    Обработка броска кубика игроками.
    """
    user_id = message.from_user.id
    dice_value = message.dice.value
    user_language = await get_language(pool, message.chat.id)
    bot = message.bot

    async with pool.acquire() as connection:
        game = await connection.fetchrow("""
            SELECT * FROM game_dice
            WHERE (player1_id = $1 OR player2_id = $1) AND is_closed = FALSE
        """, user_id)

        if not game:
            await message.reply(dice_translation["user_no_game_msg"][user_language])
            return

        game_id = game["id"]
        chat_id = game["chat_id"]
        
        if message.chat.id != chat_id:
            await message.reply(dice_translation["error_already_in_game_msg"][user_language])
            return
        
        player2_username = (await bot.get_chat(game["player2_id"])).username
        
        if game["player2_id"] is None:
            await message.reply(dice_translation["wait_second_player"][user_language])
            return

        if game["player1_id"] == user_id:
            if game["number1"] is not None:
                await message.reply(dice_translation["already_roll_dice"][user_language])
                return

            await connection.execute("""
                UPDATE game_dice
                SET number1 = $1, time_after_first_roll = $2
                WHERE id = $3
            """, dice_value, datetime.now(), game_id)

            await message.reply(dice_translation["first_result"][user_language].format(dice_value=dice_value, user_name=player2_username))

        elif game["player2_id"] == user_id:
            if game["number1"] is None:
                await message.reply(dice_translation["wait_first_player"][user_language])
                return

            if game["number2"] is not None:
                await message.reply(dice_translation["already_roll_dice_second_player"][user_language])
                return

            await connection.execute("""
                UPDATE game_dice
                SET number2 = $1, is_closed = TRUE
                WHERE id = $2
            """, dice_value, game_id)

            await message.reply(dice_translation["second_result"][user_language].format(dice_value=dice_value))
            
            await asyncio.sleep(1)

            try:
                result_message = await determine_winner(pool, game_id, user_language, bot)
                await message.answer(result_message)
            except Exception as e:
                await connection.execute("""
                    UPDATE game_dice
                    SET is_closed = TRUE
                    WHERE id = $1
                """, game_id)
                await message.answer(dice_translation["critical_error"][user_language])

                logging.error(f"Error determining winner for game {game_id}: {e}", exc_info=True)

async def determine_winner(pool, game_id, user_language, bot):
    """
    Определяет победителя офлайн-игры.
    """
    player1_id, player2_id, winner_id, loser_id, bet = await process_game_result(pool, game_id)

    if player1_id is None or player2_id is None:
        return dice_translation["game_is_not_end"][user_language]

    player1_username = (await bot.get_chat(player1_id)).username
    player2_username = (await bot.get_chat(player2_id)).username

    if winner_id == player1_id:
        winner_message = dice_translation["first_player_winner"][user_language].format(
            winner_name=player1_username, bet=bet
        )
    elif winner_id == player2_id:
        winner_message = dice_translation["second_player_winner"][user_language].format(
            winner_name=player2_username, bet=bet
        )
    else:
        winner_message = dice_translation["draw_msg"][user_language]

    return f"{winner_message}\n" + dice_translation["game_end"][user_language]

from datetime import datetime
import logging
from aiogram.types import Message
from aiogram import Bot
import asyncio
from finance.account import account_addition, account_withdrawal
from games.dice.game_result import process_game_result
from localisation.get_language import get_language
from localisation.translations.dice import translations as dice_translation

async def handle_dice_online_roll(pool, message: Message):
    """
    Обработка броска кубика в онлайн-играх.
    """
    user_id = message.from_user.id
    dice_value = message.dice.value
    user_language = await get_language(pool, user_id)
    bot: Bot = message.bot

    async with pool.acquire() as connection:
        game = await connection.fetchrow("""
            SELECT * FROM game_dice
            WHERE (player1_id = $1 OR player2_id = $1) AND is_closed = FALSE AND online = TRUE
        """, user_id)

        if not game:
            await message.reply(dice_translation["user_no_game_msg"][user_language])
            return

        game_id = game["id"]
        player1_id = game["player1_id"]
        player2_id = game["player2_id"]
        player1_language = await get_language(pool, game["player1_id"])
        player2_language = await get_language(pool, game["player2_id"])
        player1_username = (await bot.get_chat(player1_id)).username

        if not player2_id:
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
            

            await bot.send_message(
                chat_id=player1_id,
                text=dice_translation["first_result_online"][user_language].format(
                    dice_value=dice_value, user_name=player1_username
                )
            )

            await bot.forward_message(
                chat_id=player2_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            await bot.send_message(
                chat_id=player2_id,
                text=dice_translation["first_player_rolled"][player2_language].format(
                    user_name=player1_username, dice_value=dice_value
                )
            )

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

            await bot.forward_message(
                chat_id=player1_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            await bot.send_message(
                chat_id=player2_id,
                text=dice_translation["second_result"][user_language].format(
                    dice_value=dice_value
                )
            )

            await asyncio.sleep(1)

            try:
                result_message = await determine_online_winner(pool, game_id, user_language, player1_language, player2_language, bot)
                await bot.send_message(player1_id, result_message[0])
                await bot.send_message(player2_id, result_message[1])
            except Exception as e:
                await connection.execute("""
                    UPDATE game_dice
                    SET is_closed = TRUE
                    WHERE id = $1
                """, game_id)
                error_message = dice_translation["critical_error"][user_language]
                await bot.send_message(player1_id, error_message)
                await bot.send_message(player2_id, error_message)

                logging.error(f"Error determining winner for online game {game_id}: {e}", exc_info=True)

async def determine_online_winner(pool, game_id, user_language, player1_language,  player2_language, bot):
    """
    Определяет победителя онлайн-игры.
    """
    player1_id, player2_id, winner_id, loser_id, bet = await process_game_result(pool, game_id)

    if player1_id is None or player2_id is None:
        return dice_translation["game_is_not_end"][user_language]

    player1_username = (await bot.get_chat(player1_id)).username
    player2_username = (await bot.get_chat(player2_id)).username

    if winner_id == player1_id:
        winner_message_player1 = dice_translation["first_player_winner"][player1_language].format(
            winner_name=player1_username, bet=bet
        )
        winner_message_player2 = dice_translation["first_player_winner"][player2_language].format(
            winner_name=player1_username, bet=bet
        )
    elif winner_id == player2_id:
        winner_message_player1 = dice_translation["second_player_winner"][player1_language].format(
            winner_name=player2_username, bet=bet
        )
        winner_message_player2 = dice_translation["second_player_winner"][player2_language].format(
            winner_name=player2_username, bet=bet
        )
    else:
        winner_message_player1 = dice_translation["draw_msg"][player1_language]
        winner_message_player2 = dice_translation["draw_msg"][player2_language]

    return winner_message_player1, winner_message_player2

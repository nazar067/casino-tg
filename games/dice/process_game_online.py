from datetime import datetime
import logging
from aiogram.types import Message
from aiogram import Bot
import asyncio
from finance.account import account_addition, account_withdrawal
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
        # Ищем игру, в которой пользователь участвует
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
        player1_username = (await bot.get_chat(player1_id)).username

        # Если второй игрок отсутствует
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
            

            # Сообщение первому игроку
            await bot.send_message(
                chat_id=player1_id,
                text=dice_translation["first_result"][user_language].format(
                    dice_value=dice_value, user_name=player1_username
                )
            )

            # Пересылаем эмодзи второму игроку
            await bot.forward_message(
                chat_id=player2_id,  # ID целевого чата
                from_chat_id=message.chat.id,  # ID исходного чата
                message_id=message.message_id  # ID сообщения для пересылки
            )
            await bot.send_message(
                chat_id=player2_id,
                text=dice_translation["first_player_rolled"][user_language].format(
                    user_name=player1_username, dice_value=dice_value
                )
            )
            #await bot.send_dice(chat_id=player2_id, emoji=message.dice.emoji)

        elif game["player2_id"] == user_id:
            # Проверка: первый игрок должен бросить кость первым
            if game["number1"] is None:
                await message.reply(dice_translation["wait_first_player"][user_language])
                return

            # Проверка: второй игрок уже бросал кость
            if game["number2"] is not None:
                await message.reply(dice_translation["already_roll_dice_second_player"][user_language])
                return

            # Обновляем данные второго игрока
            await connection.execute("""
                UPDATE game_dice
                SET number2 = $1, is_closed = TRUE
                WHERE id = $2
            """, dice_value, game_id)

            # Сообщение второму игроку
            await bot.send_message(
                chat_id=player2_id,
                text=dice_translation["second_result"][user_language].format(
                    dice_value=dice_value
                )
            )

            # Определяем победителя
            await asyncio.sleep(1)

            try:
                result_message = await determine_online_winner(pool, game_id, user_language, bot)
                # Отправляем результат обоим игрокам
                await bot.send_message(player1_id, result_message)
                await bot.send_message(player2_id, result_message)
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


async def determine_online_winner(pool, game_id, user_language, bot: Bot):
    """
    Определяет победителя онлайн-игры.
    """
    async with pool.acquire() as connection:
        game = await connection.fetchrow("""
            SELECT player1_id, player2_id, number1, number2, bet
            FROM game_dice
            WHERE id = $1
        """, game_id)

        if not game or game["number1"] is None or game["number2"] is None:
            return dice_translation["game_is_not_end"][user_language]

        bet = game["bet"]
        player1_id = game["player1_id"]
        player2_id = game["player2_id"]

        player1_username = (await bot.get_chat(player1_id)).username
        player2_username = (await bot.get_chat(player2_id)).username

        if game["number1"] > game["number2"]:
            winner_id = player1_id
            loser_id = player2_id
            winner_message = dice_translation["first_player_winner"][user_language].format(
                winner_name=player1_username, bet=bet
            )
        elif game["number1"] < game["number2"]:
            winner_id = player2_id
            loser_id = player1_id
            winner_message = dice_translation["second_player_winner"][user_language].format(
                winner_name=player2_username, bet=bet
            )
        else:
            winner_id = None
            loser_id = None
            winner_message = dice_translation["draw_msg"][user_language]

        if winner_id and loser_id:
            await account_withdrawal(pool, loser_id, bet)
            await account_addition(pool, winner_id, bet)

        await connection.execute("""
            UPDATE game_dice
            SET winner_id = $1, is_closed = TRUE
            WHERE id = $2
        """, winner_id, game_id)

        return f"{winner_message}\n" + dice_translation["game_end"][user_language]

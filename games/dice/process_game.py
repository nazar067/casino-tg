from aiogram.types import Message
from aiogram import Router
import asyncio
from finance.account import account_addition, account_withdrawal
from localisation.check_language import check_language
from localisation.translations.dice import translations as dice_translation

router = Router()

async def handle_dice_roll(pool, message: Message):
    """
    Обработка броска кубика игроками.
    """
    user_id = message.from_user.id
    dice_value = message.dice.value
    user_language = await check_language(pool, message.chat.id)

    async with pool.acquire() as connection:
        game = await connection.fetchrow("""
            SELECT * FROM gameDice
            WHERE (player1_id = $1 OR player2_id = $1) AND is_closed = FALSE
        """, user_id)

        if not game:
            await message.reply(dice_translation["user_no_game_msg"][user_language])
            return

        game_id = game["id"]

        if game["player1_id"] == user_id:
            if game["number1"] is not None:
                await message.reply(dice_translation["already_roll_dice"][user_language])
                return

            await connection.execute("""
                UPDATE gameDice
                SET number1 = $1
                WHERE id = $2
            """, dice_value, game_id)

            await message.reply(dice_translation["first_result"][user_language].format(dice_value=dice_value))

        elif game["player2_id"] == user_id:
            if game["number1"] is None:
                await message.reply(dice_translation["wait_first_player"][user_language])
                return

            if game["number2"] is not None:
                await message.reply(dice_translation["already_roll_dice_second_player"][user_language])
                return

            await connection.execute("""
                UPDATE gameDice
                SET number2 = $1, is_closed = TRUE
                WHERE id = $2
            """, dice_value, game_id)

            await message.reply(dice_translation["second_result"][user_language].format(dice_value=dice_value))
            
            await asyncio.sleep(1)

            result_message = await determine_winner(pool, game_id, user_language)
            await message.answer(result_message)

async def determine_winner(pool, game_id, user_language):
    """
    Определяет победителя игры.
    """
    async with pool.acquire() as connection:
        game = await connection.fetchrow("""
            SELECT player1_id, player2_id, number1, number2, bet
            FROM gameDice
            WHERE id = $1
        """, game_id)

        if not game or game["number1"] is None or game["number2"] is None:
            return dice_translation["game_is_not_end"][user_language]

        bet = game["bet"]
        player1_id = game["player1_id"]
        player2_id = game["player2_id"]
        
        if game["number1"] > game["number2"]:
            winner_id = player1_id
            loser_id = player2_id
            winner_message = dice_translation["first_player_winner"][user_language].format(winner_id=winner_id)
        elif game["number1"] < game["number2"]:
            winner_id = player2_id
            loser_id = player1_id
            winner_message = dice_translation["second_player_winner"][user_language].format(winner_id=winner_id)
        else:
            winner_id = None
            loser_id = None
            winner_message = dice_translation["draw_msg"][user_language]

        if winner_id and loser_id:
            await account_addition(pool, winner_id, bet)
            await account_withdrawal(pool, loser_id, bet)

        await connection.execute("""
            UPDATE gameDice
            SET winner_id = $1, is_closed = TRUE
            WHERE id = $2
        """, winner_id, game_id)

        return f"{winner_message}\n" + dice_translation["game_end"][user_language]
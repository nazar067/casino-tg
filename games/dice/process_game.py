from aiogram.types import Message
from aiogram import Router
from datetime import datetime
from finance.account import account_addition, account_withdrawal

router = Router()

async def handle_dice_roll(pool, message: Message):
    """
    Обработка броска кубика игроками.
    """
    user_id = message.from_user.id
    dice_value = message.dice.value

    async with pool.acquire() as connection:
        # Проверяем активную игру
        game = await connection.fetchrow("""
            SELECT * FROM gameDice
            WHERE (player1_id = $1 OR player2_id = $1) AND is_closed = FALSE
        """, user_id)

        if not game:
            await message.reply("⚠️ Вы сейчас не участвуете в активной игре.")
            return

        game_id = game["id"]

        if game["player1_id"] == user_id:
            if game["number1"] is not None:
                await message.reply("⚠️ Вы уже бросили кубик. Ждём броска второго игрока.")
                return

            await connection.execute("""
                UPDATE gameDice
                SET number1 = $1
                WHERE id = $2
            """, dice_value, game_id)

            await message.reply(f"🎲 Вы выбросили: {dice_value}. Ожидаем броска второго игрока.")

        elif game["player2_id"] == user_id:
            if game["number1"] is None:
                await message.reply("⚠️ Первый игрок ещё не бросил кубик.")
                return

            if game["number2"] is not None:
                await message.reply("⚠️ Вы уже бросили кубик. Ожидайте результата.")
                return

            await connection.execute("""
                UPDATE gameDice
                SET number2 = $1, is_closed = TRUE
                WHERE id = $2
            """, dice_value, game_id)

            await message.reply(f"🎲 Вы выбросили: {dice_value}. Определяем победителя...")

            result_message = await determine_winner(pool, game_id)
            await message.answer(result_message)

async def determine_winner(pool, game_id):
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
            return "⚠️ Невозможно определить победителя: игра не завершена."

        bet = game["bet"]
        player1_id = game["player1_id"]
        player2_id = game["player2_id"]
        
        if game["number1"] > game["number2"]:
            winner_id = player1_id
            loser_id = player2_id
            winner_message = f"🎉 Победитель: Игрок 1 (ID: {winner_id})! 🎲"
        elif game["number1"] < game["number2"]:
            winner_id = player2_id
            loser_id = player1_id
            winner_message = f"🎉 Победитель: Игрок 2 (ID: {winner_id})! 🎲"
        else:
            winner_id = None
            loser_id = None
            winner_message = "🎲 Ничья! Оба игрока выбросили одинаковые числа."

        # Если есть победитель и проигравший
        if winner_id and loser_id:
            # Победителю добавляем выигрыш
            await account_addition(pool, winner_id, bet)
            # У проигравшего снимаем ставку
            await account_withdrawal(pool, loser_id, bet)

        # Обновляем информацию о победителе
        await connection.execute("""
            UPDATE gameDice
            SET winner_id = $1, is_closed = TRUE
            WHERE id = $2
        """, winner_id, game_id)

        return f"{winner_message}\nИгра завершена!"
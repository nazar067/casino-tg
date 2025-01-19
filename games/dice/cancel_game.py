import logging
from aiogram.types import CallbackQuery, Message
from aiogram import Bot, Router
from datetime import datetime, timedelta, timezone
from asyncpg import Pool
import asyncio

from finance.account import account_addition
from localisation.translations.dice import translations as dice_translation
from localisation.get_language import get_language

router = Router()

async def cancel_game_handler(callback: CallbackQuery, pool, state):
    """
    Обработка кнопки отмены игры.
    """
    user_id = callback.from_user.id
    game_id = int(callback.data.split(":")[1])
    chat_id = callback.message.chat.id
    user_language = await get_language(pool, chat_id)

    async with pool.acquire() as connection:
        game = await connection.fetchrow("""
            SELECT * FROM gameDice WHERE id = $1 AND is_closed = FALSE
        """, game_id)

        if not game:
            await callback.answer(dice_translation["cancel_error_msg"][user_language], show_alert=True)
            return

        if game["player1_id"] != user_id:
            await callback.answer(dice_translation["cancel_creator_error_msg"][user_language], show_alert=True)
            return

        # Удаляем игру из базы данных
        await connection.execute("""
            DELETE FROM gameDice WHERE id = $1
        """, game_id)

    # Извлекаем данные из состояния
    data = await state.get_data()
    creator_message_id = data.get("creator_message_id")
    game_message_id = data.get("game_message_id")

    # Удаляем сообщения
    try:
        if creator_message_id:
            await callback.bot.delete_message(callback.message.chat.id, creator_message_id)
    finally:    
        if game_message_id:
            await callback.bot.delete_message(callback.message.chat.id, game_message_id)

    # Очищаем состояние
    await state.clear()
    await callback.answer(dice_translation["cancel_success_msg"][user_language])

async def check_game_status(pool, bot):
    """
    Проверяет статус игр и отправляет напоминания/обновления.
    """
    async with pool.acquire() as connection:
        now = datetime.now()

        # Удаляем игры, где никто не бросил кубик в течение 10 минут
        expiration_time_no_moves = now - timedelta(minutes=10)
        expired_games_no_moves = await connection.fetch("""
            SELECT id, chat_id 
            FROM gameDice
            WHERE is_closed = FALSE AND number1 IS NULL AND timestamp <= $1
        """, expiration_time_no_moves)

        for game in expired_games_no_moves:
            await bot.send_message(
                chat_id=game["chat_id"],
                text="⏳ Игра была отменена, так как никто не бросил кость за 10 минут."
            )

        if expired_games_no_moves:
            expired_ids = [game["id"] for game in expired_games_no_moves]
            await connection.execute("""
                DELETE FROM gameDice
                WHERE id = ANY($1::int[])
            """, expired_ids)

        # Напоминания через 5 минут после первого броска (если предупреждение не отправлено)
        warning_time = now - timedelta(minutes=5)
        games_to_warn = await connection.fetch("""
            SELECT id, chat_id 
            FROM gameDice
            WHERE is_closed = FALSE AND number1 IS NOT NULL 
            AND number2 IS NULL AND time_after_first_roll <= $1
            AND warning_sent = FALSE
        """, warning_time)

        for game in games_to_warn:
            await bot.send_message(
                chat_id=game["chat_id"],
                text="⚠️ Второй игрок, если вы не бросите кость в течение 5 минут, вы проиграете."
            )

            # Обновляем поле warning_sent, чтобы сообщение не отправлялось повторно
            await connection.execute("""
                UPDATE gameDice
                SET warning_sent = TRUE
                WHERE id = $1
            """, game["id"])

        # Завершение игр через 10 минут после первого броска
        expiration_time = now - timedelta(minutes=10)
        expired_games = await connection.fetch("""
            SELECT id, chat_id, player1_id, bet 
            FROM gameDice
            WHERE is_closed = FALSE AND number1 IS NOT NULL 
            AND number2 IS NULL AND time_after_first_roll <= $1
        """, expiration_time)

        for game in expired_games:
            await award_first_player_as_winner(pool, bot, game["id"], game["player1_id"], game["bet"], game["chat_id"])

async def award_first_player_as_winner(pool, bot, game_id, player1_id, bet, chat_id):
    """
    Присуждает победу первому игроку, если второй игрок не бросил кубик в течение 10 минут.
    """
    async with pool.acquire() as connection:
        try:
            # Начисляем ставку первому игроку
            await account_addition(pool, player1_id, bet)

            # Обновляем статус игры и устанавливаем победителя
            await connection.execute("""
                UPDATE gameDice
                SET is_closed = TRUE, winner_id = $1
                WHERE id = $2
            """, player1_id, game_id)

            # Отправляем сообщение в чат
            await bot.send_message(
                chat_id=chat_id,
                text="⏳ Время истекло! Второй игрок не бросил кость. Первый игрок победил."
            )
        except Exception as e:
            logging.error(f"Error awarding game {game_id} to player {player1_id}: {e}")


async def periodic_cleanup(pool, bot, interval=60):
    """
    Периодически запускает проверку статуса игр.
    """
    while True:
        try:
            await check_game_status(pool, bot)
        except Exception as e:
            logging.error(f"Ошибка при проверке игр: {e}")
        await asyncio.sleep(interval)
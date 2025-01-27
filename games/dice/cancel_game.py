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
            SELECT * FROM game_dice WHERE id = $1 AND is_closed = FALSE
        """, game_id)

        if not game:
            await callback.answer(dice_translation["cancel_error_msg"][user_language], show_alert=True)
            return

        if game["player1_id"] != user_id:
            await callback.answer(dice_translation["cancel_creator_error_msg"][user_language], show_alert=True)
            return

        await connection.execute("""
            DELETE FROM game_dice WHERE id = $1
        """, game_id)

    data = await state.get_data()
    creator_message_id = data.get("creator_message_id")
    game_message_id = data.get("game_message_id")

    try:
        if creator_message_id:
            await callback.bot.delete_message(callback.message.chat.id, creator_message_id)
    finally:    
        if game_message_id:
            await callback.bot.delete_message(callback.message.chat.id, game_message_id)

    await state.clear()
    await callback.answer(dice_translation["cancel_success_msg"][user_language])

async def check_game_status(pool, bot):
    """
    Проверяет статус игр и отправляет напоминания/обновления.
    """
    async with pool.acquire() as connection:
        now = datetime.now()

        expiration_time_no_moves = now - timedelta(minutes=10)
        expired_games_no_moves = await connection.fetch("""
            SELECT id, chat_id, start_msg_id, online, player2_id
            FROM game_dice
            WHERE is_closed = FALSE AND number1 IS NULL AND timestamp <= $1
        """, expiration_time_no_moves)

        for game in expired_games_no_moves:
            user_language = await get_language(pool, game["chat_id"])
            if game["online"] is True:
                player2_language = await get_language(pool, game["player2_id"])
                await bot.send_message(
                    chat_id=game["player2_id"],
                    text=dice_translation["time_out"][player2_language]
                )
            await bot.send_message(
                chat_id=game["chat_id"],
                text=dice_translation["time_out"][user_language]
            )

            try:
                await bot.delete_message(chat_id=game["chat_id"], message_id=game["start_msg_id"])
            except Exception as e:
                logging.warning(f"Unable to delete message {game['start_msg_id']} in chat {game['chat_id']}: {e}")

        if expired_games_no_moves:
            expired_ids = [game["id"] for game in expired_games_no_moves]
            await connection.execute("""
                DELETE FROM game_dice
                WHERE id = ANY($1::int[])
            """, expired_ids)

        warning_time = now - timedelta(minutes=5)
        games_to_warn = await connection.fetch("""
            SELECT id, chat_id, player2_id, online
            FROM game_dice
            WHERE is_closed = FALSE AND number1 IS NOT NULL 
            AND number2 IS NULL AND time_after_first_roll <= $1
            AND warning_sent = FALSE
        """, warning_time)

        for game in games_to_warn:
            user_language = await get_language(pool, game["chat_id"])
            player2_id = game["player2_id"]
            if not player2_id:
                logging.warning(f"Game {game['id']} has no second player.")
                continue
            if game["online"] is True:
                player2_language = await get_language(pool, player2_id)
                await bot.send_message(
                    chat_id=player2_id,
                    text=dice_translation["warning_for_second_player_online"][player2_language]
                )
                await connection.execute("""
                    UPDATE game_dice
                    SET warning_sent = TRUE
                    WHERE id = $1
                """, game["id"])
                continue

            player2_username = (await bot.get_chat(player2_id)).username

            await bot.send_message(
                chat_id=game["chat_id"],
                text=dice_translation["warning_for_second_player"][user_language].format(second_player=player2_username)
            )

            await connection.execute("""
                UPDATE game_dice
                SET warning_sent = TRUE
                WHERE id = $1
            """, game["id"])

        expiration_time = now - timedelta(minutes=10)
        expired_games = await connection.fetch("""
            SELECT id, chat_id, player1_id, bet, player2_id, online
            FROM game_dice
            WHERE is_closed = FALSE AND number1 IS NOT NULL 
            AND number2 IS NULL AND time_after_first_roll <= $1
        """, expiration_time)

        for game in expired_games:
            await award_first_player_as_winner(
                pool, bot, game["id"], game["player1_id"], game["bet"], game["chat_id"], game["player2_id"], game["online"]
            )

async def award_first_player_as_winner(pool, bot, game_id, player1_id, bet, chat_id, player2_id, online):
    """
    Присуждает победу первому игроку, если второй игрок не бросил кубик в течение 10 минут.
    """
    async with pool.acquire() as connection:
        try:
            user_language = await get_language(pool, chat_id)
            player2_language = await get_language(pool, player2_id)
            player1_username = (await bot.get_chat(player1_id)).username
            player2_username = (await bot.get_chat(player2_id)).username
            
            await account_addition(pool, player1_id, bet)

            await connection.execute("""
                UPDATE game_dice
                SET is_closed = TRUE, winner_id = $1
                WHERE id = $2
            """, player1_id, game_id)

            if online is True:
                await bot.send_message(
                    chat_id=player2_id,
                    text=dice_translation["first_player_auto_win"][player2_language].format(second_player=player2_username, first_player=player1_username, bet=bet*2)
                )
            
            await bot.send_message(
                chat_id=chat_id,
                text=dice_translation["first_player_auto_win"][user_language].format(second_player=player2_username, first_player=player1_username, bet=bet*2)
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
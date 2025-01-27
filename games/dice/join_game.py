from aiogram.types import CallbackQuery
from aiogram import Bot, Router
import logging

from games.dice.check_active_game import has_active_game
from localisation.translations.dice import translations as dice_translation
from user.balance import get_user_balance
from localisation.get_language import get_language

router = Router()

async def join_game_handler(callback: CallbackQuery, pool, online: bool = False):
    """
    Обработчик для присоединения к игре (онлайн или офлайн).

    :param callback: Объект CallbackQuery.
    :param pool: Пул соединений к базе данных.
    :param online: Если True, то игра в онлайн-режиме, иначе в офлайн-режиме.
    """
    try:
        game_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id if not online else user_id
        bot = callback.message.bot
        chat_language = await get_language(pool, chat_id)
        
        if not pool:
            if online:
                await bot.send_message(user_id, "Ошибка: подключение к базе данных отсутствует.")
            else:
                await callback.answer("Ошибка: подключение к базе данных отсутствует.", show_alert=True)
            return

        if await has_active_game(pool, user_id):
            if online:
                await bot.send_message(user_id, dice_translation["error_already_in_game_msg"][chat_language])
            else:
                await callback.answer(dice_translation["error_already_in_game_msg"][chat_language], show_alert=True)
            return

        async with pool.acquire() as connection:
            game = await connection.fetchrow("""
                SELECT * FROM game_dice WHERE id = $1 AND is_closed = FALSE
            """, game_id)
            await bot.delete_message(chat_id=game["chat_id"], message_id=game["start_msg_id"])
            player1_language = await get_language(pool, game['player1_id'])
            
            if not game:
                if online:
                    await bot.send_message(user_id, dice_translation["game_not_found_msg"][chat_language])
                else:
                    await callback.answer(dice_translation["game_not_found_msg"][chat_language], show_alert=True)
                return

            if game["player1_id"] == user_id:
                if online:
                    await bot.send_message(user_id, dice_translation["error_connect_your_game_msg"][chat_language])
                else:
                    await callback.answer(dice_translation["error_connect_your_game_msg"][chat_language], show_alert=True)
                return

            if game["player2_id"] is not None:
                if online:
                    await bot.send_message(user_id, dice_translation["error_is_second_player_msg"][chat_language])
                else:
                    await callback.answer(dice_translation["error_is_second_player_msg"][chat_language], show_alert=True)
                return

            user_balance = await get_user_balance(pool, user_id)
            if user_balance < game["bet"]:
                if online:
                    await bot.send_message(user_id, dice_translation["join_no_stars_msg"][chat_language])
                else:
                    await callback.answer(dice_translation["join_no_stars_msg"][chat_language], show_alert=True)
                return

            await connection.execute("""
                UPDATE game_dice
                SET player2_id = $1
                WHERE id = $2
            """, user_id, game_id)
            
        player1_username = (await bot.get_chat(game['player1_id'])).username
        player2_username = callback.from_user.username

        new_message_text_player1 = dice_translation["game_start_online1_msg"][player1_language].format(
            game_id=game_id, bet=game["bet"], player1_id=player1_username, user_id=player2_username
        )
        new_message_text_player2 = dice_translation["game_start_online2_msg"][chat_language].format(
            game_id=game_id, bet=game["bet"], player1_id=player1_username, user_id=player2_username
        )
        new_message_text_offline = dice_translation["game_start_msg"][chat_language].format(
            game_id=game_id, player1_id=player1_username, user_id=player2_username
        )

        if online:
            await bot.send_message(game["player1_id"], new_message_text_player1)
            await bot.send_message(user_id, new_message_text_player2)
        else:
            try:
                await callback.message.delete()
            except Exception as e:
                logging.error(f"Error deleting start message {game_id}: {e}", exc_info=True)

            await callback.message.answer(new_message_text_offline)

        if not online and callback.message:
            await callback.answer(dice_translation["succes_join_msg"][chat_language])
    except Exception as e:
        logging.error(f"Error in join_game_handler: {e}", exc_info=True)
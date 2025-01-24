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
        # Извлекаем game_id из данных callback
        game_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id if not online else user_id
        bot = callback.message.bot
        user_language = await get_language(pool, chat_id)
        
        if not pool:
            if online:
                await bot.send_message(user_id, "Ошибка: подключение к базе данных отсутствует.")
            else:
                await callback.answer("Ошибка: подключение к базе данных отсутствует.", show_alert=True)
            return

        # Проверяем, участвует ли пользователь уже в игре
        if await has_active_game(pool, user_id):
            if online:
                await bot.send_message(user_id, dice_translation["error_already_in_game_msg"][user_language])
            else:
                await callback.answer(dice_translation["error_already_in_game_msg"][user_language], show_alert=True)
            return

        async with pool.acquire() as connection:
            # Получаем данные игры
            game = await connection.fetchrow("""
                SELECT * FROM game_dice WHERE id = $1 AND is_closed = FALSE
            """, game_id)

            if not game:
                if online:
                    await bot.send_message(user_id, dice_translation["game_not_found_msg"][user_language])
                else:
                    await callback.answer(dice_translation["game_not_found_msg"][user_language], show_alert=True)
                return

            if game["player1_id"] == user_id:
                if online:
                    await bot.send_message(user_id, dice_translation["error_connect_your_game_msg"][user_language])
                else:
                    await callback.answer(dice_translation["error_connect_your_game_msg"][user_language], show_alert=True)
                return

            if game["player2_id"] is not None:
                if online:
                    await bot.send_message(user_id, dice_translation["error_is_second_player_msg"][user_language])
                else:
                    await callback.answer(dice_translation["error_is_second_player_msg"][user_language], show_alert=True)
                return

            # Проверяем баланс пользователя
            user_balance = await get_user_balance(pool, user_id)
            if user_balance < game["bet"]:
                if online:
                    await bot.send_message(user_id, dice_translation["join_no_stars_msg"][user_language])
                else:
                    await callback.answer(dice_translation["join_no_stars_msg"][user_language], show_alert=True)
                return

            # Обновляем данные игры
            await connection.execute("""
                UPDATE game_dice
                SET player2_id = $1
                WHERE id = $2
            """, user_id, game_id)

        # Получаем имена игроков
        player1_username = (await bot.get_chat(game['player1_id'])).username
        player2_username = callback.from_user.username

        new_message_text = dice_translation["game_start_msg"][user_language].format(
            game_id=game_id, player1_id=player1_username, user_id=player2_username
        )

        if online:
            # Отправляем сообщение каждому игроку в ЛС
            await bot.send_message(game["player1_id"], new_message_text)
            await bot.send_message(user_id, new_message_text)
        else:
            # Удаляем старое сообщение и отправляем новое в группе
            try:
                await callback.message.delete()
            except Exception as e:
                logging.error(f"Error deleting start message {game_id}: {e}", exc_info=True)

            await callback.message.answer(new_message_text)

        # Отправляем ответ пользователю
        if not online and callback.message:
            await callback.answer(dice_translation["succes_join_msg"][user_language])
    except Exception as e:
        logging.error(f"Error in join_game_handler: {e}", exc_info=True)
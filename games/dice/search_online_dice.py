from aiogram.types import CallbackQuery, Message
import logging

from games.dice.join_game import join_game_handler

async def search_dice(pool, bot, message, min_bet: int, max_bet: int):
    """
    Ищет доступные онлайн игры и автоматически присоединяет второго игрока.

    :param pool: Пул соединений с базой данных.
    :param bot: Экземпляр бота.
    :param user_context: Объект Message или CallbackQuery для получения user_id.
    :param min_bet: Минимальная ставка для поиска игр.
    :param max_bet: Максимальная ставка для поиска игр.
    """
    try:
        # Получаем user_id из user_context
        if isinstance(message, Message):
            user_id = message.from_user.id
            chat_id = message.chat.id
        elif isinstance(message, CallbackQuery):
            user_id = message.from_user.id
            chat_id = message.message.chat.id
        else:
            raise ValueError("Invalid user context provided. Must be Message or CallbackQuery.")

        async with pool.acquire() as connection:
            # Ищем подходящие игры
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

            if not game:
                await bot.send_message(chat_id, "Нет доступных игр в данный момент.")
                logging.info(f"No available games found for user {user_id} in the range {min_bet}-{max_bet}.")
                return

            game_id = game["id"]
            bet = game["bet"]

            # Создаем объект CallbackQuery для вызова join_game_handler
            fake_callback = CallbackQuery(
                id="search_dice_callback",
                from_user=message.from_user,
                message=message,
                chat_instance="fake_instance",
                data=f"join_game:{game_id}"
            )

            # Присоединяем пользователя к игре
            await join_game_handler(fake_callback, pool, bot)
    except Exception as e:
        logging.error(f"Error in search_dice: {e}", exc_info=True)

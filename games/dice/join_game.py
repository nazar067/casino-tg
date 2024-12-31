from aiogram.types import CallbackQuery
from aiogram import Router

from localisation.translations import translations
from user.balance import get_user_balance
from localisation.check_language import check_language

router = Router()

async def join_game_handler(callback: CallbackQuery, pool):
    """
    Обработчик для присоединения к игре.
    """
    game_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    user_language = await check_language(pool, chat_id)
    
    if not pool:
        await callback.answer("Ошибка: подключение к базе данных отсутствует.", show_alert=True)
        return

    async with pool.acquire() as connection:
        game = await connection.fetchrow("""
            SELECT * FROM gameDice WHERE id = $1 AND is_closed = FALSE
        """, game_id)

        if not game:
            await callback.answer(translations["game_not_found_msg"][user_language], show_alert=True)
            return

        if game["player1_id"] == user_id:
            await callback.answer(translations["error_connect_your_game_msg"][user_language], show_alert=True)
            return

        if game["player2_id"] is not None:
            await callback.answer(translations["error_is_second_player_msg"][user_language], show_alert=True)
            return

        user_balance = await get_user_balance(pool, user_id)
        if user_balance < game["bet"]:
            await callback.answer(translations["join_no_stars_msg"][user_language], show_alert=True)
            return

        # Обновляем данные игры
        await connection.execute("""
            UPDATE gameDice
            SET player2_id = $1
            WHERE id = $2
        """, user_id, game_id)

    await callback.message.edit_text(
        translations["game_start_msg"][user_language].format(game_id=game_id, player1_id=game['player1_id'], user_id=user_id)
    )
    await callback.answer("Вы успешно присоединились к игре!")

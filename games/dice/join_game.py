from aiogram.types import CallbackQuery
from aiogram import Router

from user.balance import get_user_balance

router = Router()

async def join_game_handler(callback: CallbackQuery, pool):
    """
    Обработчик для присоединения к игре.
    """
    game_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    if not pool:
        await callback.answer("Ошибка: подключение к базе данных отсутствует.", show_alert=True)
        return

    async with pool.acquire() as connection:
        game = await connection.fetchrow("""
            SELECT * FROM gameDice WHERE id = $1 AND is_closed = FALSE
        """, game_id)

        if not game:
            await callback.answer("⚠️ Игра не найдена или уже завершена.", show_alert=True)
            return

        if game["player1_id"] == user_id:
            await callback.answer("⚠️ Вы не можете присоединиться к своей игре.", show_alert=True)
            return

        if game["player2_id"] is not None:
            await callback.answer("⚠️ У этой игры уже есть второй игрок.", show_alert=True)
            return

        user_balance = await get_user_balance(pool, user_id)
        if user_balance < game["bet"]:
            await callback.answer("⚠️ Недостаточно звёзд для присоединения к игре.", show_alert=True)
            return

        # Обновляем данные игры
        await connection.execute("""
            UPDATE gameDice
            SET player2_id = $1
            WHERE id = $2
        """, user_id, game_id)

    await callback.message.edit_text(
        f"🎲 Игра #{game_id} готова!\n\nИгрок 1: {game['player1_id']}\nИгрок 2: {user_id}\n\nОжидайте начала игры."
    )
    await callback.answer("Вы успешно присоединились к игре!")

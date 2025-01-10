from aiogram.types import CallbackQuery, Message
from aiogram import Router

from localisation.translations.dice import translations as dice_translation
from localisation.check_language import check_language

router = Router()

async def cancel_game_handler(callback: CallbackQuery, pool, state):
    """
    Обработка кнопки отмены игры.
    """
    user_id = callback.from_user.id
    game_id = int(callback.data.split(":")[1])
    chat_id = callback.message.chat.id
    user_language = await check_language(pool, chat_id)

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
        try:
            if creator_message_id:
                await callback.bot.delete_message(callback.message.chat.id, creator_message_id)
        finally:    
            if game_message_id:
                await callback.bot.delete_message(callback.message.chat.id, game_message_id)
    except Exception as e:
        print(f"Ошибка удаления сообщений: {e}")

    # Очищаем состояние
    await state.clear()
    await callback.answer(dice_translation["cancel_success_msg"][user_language])

# games/cancel_game.py
from aiogram.types import CallbackQuery
from aiogram import Router
from games.dice.register_game import active_games

router = Router()

@router.callback_query(lambda callback: callback.data.startswith("cancel_game:"))
async def cancel_game_handler(callback: CallbackQuery):
    """
    Обработчик для отмены игры.
    """
    game_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    # Проверяем, существует ли игра
    if game_id not in active_games:
        await callback.answer("⚠️ Игра не найдена или уже завершена.", show_alert=True)
        return

    game = active_games[game_id]

    # Проверяем, что только создатель игры может её отменить
    if game["creator"] != user_id:
        await callback.answer("⚠️ Только создатель игры может её отменить.", show_alert=True)
        return

    # Удаляем игру из активных
    del active_games[game_id]

    await callback.message.edit_text(f"❌ Игра #{game_id} была отменена создателем.")
    await callback.answer()

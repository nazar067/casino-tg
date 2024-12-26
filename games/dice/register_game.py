from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Dispatcher, Router
from aiogram.fsm.context import FSMContext

from keyboards.keyboard import join_dice_button
from localisation.check_language import check_language

router = Router()

async def create_game_handler(message: Message, pool, dp: Dispatcher):
    """
    Создание новой игры в кости.
    """
    user_id = message.from_user.id
    pool = dp["db_pool"]
    chat_id = message.chat.id

    user_language = await check_language(pool, chat_id)

    # Извлекаем ставку
    try:
        bet = int(message.text.split(maxsplit=1)[1])
        if bet <= 0:
            raise ValueError
    except (IndexError, ValueError):
        await message.answer("⚠️ Пожалуйста, укажите ставку после команды. Пример: /dice 100")
        return

    # Добавляем запись в базу данных
    async with pool.acquire() as connection:
        game_id = await connection.fetchval("""
            INSERT INTO gameDice (player1_id, bet)
            VALUES ($1, $2)
            RETURNING id
        """, user_id, bet)

    # Отправляем сообщение с кнопкой присоединения
    await message.answer(
        f"🎲 Игра #{game_id} создана! Ставка: {bet}.\n\nОжидаем второго игрока.",
        reply_markup=join_dice_button(game_id, bet, user_language)
    )

# Регистрация хендлеров в роутере
def setup_register_game_handlers(dp: Dispatcher):
    dp.include_router(router)

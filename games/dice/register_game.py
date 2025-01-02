from aiogram.types import Message
from aiogram import Dispatcher, Router

from localisation.translations import translations
from localisation.check_language import check_language
from user.balance import get_user_balance
from keyboards.keyboard import game_buttons

router = Router()

async def create_game_handler(message: Message, pool, state):
    """
    Создание новой игры в кости.
    """
    user_id = message.from_user.id
    user_language = await check_language(pool, message.chat.id)

    # Проверяем, участвует ли пользователь уже в игре
    async with pool.acquire() as connection:
        existing_game = await connection.fetchrow("""
            SELECT id FROM gameDice WHERE (player1_id = $1 OR player2_id = $1) AND is_closed = FALSE
        """, user_id)

    if existing_game:
        await message.answer(translations["error_already_in_game_msg"][user_language])
        return

    try:
        bet = int(message.text.split(maxsplit=1)[1])
        if bet <= 0:
            raise ValueError
    except (IndexError, ValueError):
        await message.answer(translations["register_help_msg"][user_language])
        return

    # Проверяем баланс игрока
    user_balance = await get_user_balance(pool, user_id)
    if user_balance < bet:
        await message.answer(translations["register_no_stars_msg"][user_language])
        return

    async with pool.acquire() as connection:
        game_id = await connection.fetchval("""
            INSERT INTO gameDice (player1_id, bet, is_closed)
            VALUES ($1, $2, FALSE)
            RETURNING id
        """, user_id, bet)

    # Сохраняем ID сообщения команды и добавляем в состояние
    creator_message_id = message.message_id
    game_message = await message.answer(
        translations["wait_second_player_msg"][user_language].format(game_id=game_id, bet=bet),
        reply_markup=game_buttons(game_id, bet, user_language)
    )
    game_message_id = game_message.message_id

    # Сохраняем данные игры в состояние
    await state.update_data(
        creator_message_id=creator_message_id,
        game_message_id=game_message_id,
        game_id=game_id
    )

# Регистрация хендлеров в роутере
def setup_register_game_handlers(dp: Dispatcher):
    dp.include_router(router)

from aiogram.types import Message
from aiogram import Dispatcher
from finance.withdraw import check_withdrawable_stars
from user.balance import get_user_balance
from localisation.translations import translations

async def withdraw_handler(message: Message, dp: Dispatcher):
    """
    Обработка кнопки "Вывести" из меню
    """
    pool = dp["db_pool"]
    user_id = message.from_user.id

    # Получаем сообщение о доступных звездах
    response_message = await check_withdrawable_stars(pool, user_id)

    # Отправляем сообщение пользователю
    return response_message
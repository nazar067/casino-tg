from aiogram.types import Message
from aiogram import Dispatcher
from user.balance import get_user_balance
from localisation.translations import translations

async def withdraw_handler(message: Message, dp: Dispatcher, user_language: str):
    """
    Обработка кнопки "Вывести" из меню
    """
    pool = dp["db_pool"]

    # Отправляем локализованное сообщение
    return translations["withdraw"][user_language]
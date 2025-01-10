from aiogram.types import Message
from aiogram import Dispatcher
from user.balance import get_user_balance
from localisation.translations.finance import translations

async def balance_handler(message: Message, dp: Dispatcher, user_language: str):
    """
    Обработка кнопки "Баланс" из меню
    """
    pool = dp["db_pool"]

    user_id = message.from_user.id
    
    balance = await get_user_balance(pool, user_id)
    
    return translations["balance"][user_language].format(balance=balance)
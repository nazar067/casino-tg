from aiogram.types import Message
from aiogram import Dispatcher
from keyboards.keyboard import payment_keyboard
from localisation.translations.finance import translations

async def donate_handler(message: Message, dp: Dispatcher, user_language: str)-> str:
    """
    Обработка кнопки "Пополнить" из меню
    """
    pool = dp["db_pool"]
    chat_id = message.chat.id

    return translations["donate_text"][user_language], payment_keyboard(user_language)
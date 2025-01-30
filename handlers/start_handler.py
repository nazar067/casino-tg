from aiogram.types import Message
from aiogram import Dispatcher
from localisation.set_language import set_language
from localisation.get_language import get_language
from keyboards.keyboard import menu_keyboard
from localisation.translations.general import translations
from asyncpg import Record

async def start_handler(message: Message, dp: Dispatcher):
    """
    Обработка команды /start
    """
    pool = dp["db_pool"]
    chat_id = message.chat.id
    language_code = message.from_user.language_code or "en"

    async with pool.acquire() as connection:
        existing_language: Record = await connection.fetchrow("""
            SELECT language_code FROM languages WHERE chat_id = $1
        """, chat_id)

    if not existing_language:
        if not language_code or len(language_code) != 2:
            language_code = "en"
        await set_language(pool, chat_id, language_code)
        user_language = language_code
    else:
        user_language = existing_language["language_code"]
        
    if message.chat.type != "private":
        await message.reply(
            translations["welcome"][user_language],
            reply_markup=menu_keyboard(user_language)
        )
    else:
        await message.reply(
            translations["welcome_private"][user_language],
            reply_markup=menu_keyboard(user_language)
        )

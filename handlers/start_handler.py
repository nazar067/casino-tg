from aiogram.types import Message
from aiogram import Dispatcher
from localisation.get_language import get_language
from localisation.check_language import check_language
from keyboards.keyboard import menu_keyboard
from localisation.translations.start import translations

async def start_handler(message: Message, dp: Dispatcher):
    """
    Обработка команды /start
    """
    pool = dp["db_pool"]
    chat_id = message.chat.id
    language_code = message.from_user.language_code or "en"

    if not language_code or len(language_code) != 2:
        language_code = "en"

    await get_language(pool, chat_id, language_code)

    user_language = await check_language(pool, chat_id)

    await message.reply(
        translations["welcome"][user_language],
        reply_markup=menu_keyboard(user_language)
    )
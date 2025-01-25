from aiogram.types import CallbackQuery
from aiogram.types import ReplyKeyboardMarkup
from localisation.get_language import get_language
from localisation.set_language import set_language
from localisation.translations.general import translations as general_translation
from localisation.translations.finance import translations as finance_translation
from keyboards.keyboard import menu_keyboard

async def set_language_handler(callback: CallbackQuery, pool):
    """
    Обработка нажатия кнопки для смены языка.
    """
    chat_id = callback.message.chat.id
    language_code = callback.data.split(":")[1]

    await set_language(pool, chat_id, language_code)
    user_language = await get_language(pool, chat_id)
    
    await callback.bot.delete_message(callback.message.chat.id, callback.message.message_id)

    await callback.answer(general_translation["success_lang"][user_language])
    
    await callback.message.answer(
        general_translation["updated_menu"][user_language],
        reply_markup=menu_keyboard(user_language)
    )

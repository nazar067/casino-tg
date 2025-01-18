from aiogram.types import CallbackQuery

from localisation.get_language import get_language
from localisation.set_language import set_language
from localisation.translations.general import translations as general_translation

async def set_language_handler(callback: CallbackQuery, pool):
    """
    Обработка нажатия кнопки для смены языка.
    """
    chat_id = callback.message.chat.id
    language_code = callback.data.split(":")[1]

    await set_language(pool, chat_id, language_code)
    user_language = await get_language(pool, callback.message.chat.id)

    await callback.answer(general_translation["success_lang"][user_language])

    await callback.message.edit_text(
        general_translation["msg_for_update_btns"][user_language],
        reply_markup=None
    )

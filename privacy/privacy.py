import re
from aiogram.types import Message

from localisation.get_language import get_language
from localisation.translations.general import translations as general_translation

async def get_privacy(message: Message, dp):
    """
    Отправка политики конфиденциальности с правильным форматированием MarkdownV2.
    """
    pool = dp["db_pool"]
    chat_id = message.chat.id
    user_language = await get_language(pool, chat_id)

    # Отправляем сообщение
    await message.reply(
        general_translation["privacy"][user_language],
        parse_mode="MarkdownV2"
    )
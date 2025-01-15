from aiogram.types import Message, CallbackQuery
from aiogram import Router
import re
from user.transactions import get_user_transactions
from localisation.check_language import check_language
from localisation.translations.finance import translations as finance_translation
from keyboards.keyboard import pagination_keyboard

router = Router()

PAGE_SIZE = 10

async def history_handler(message_or_callback, pool, page: int = 1):
    """
    Обработка кнопки "История" для отображения транзакций пользователя с пагинацией.
    """
    user_id, chat_id, is_callback = extract_user_and_chat_data(message_or_callback)

    user_language = await check_language(pool, chat_id)

    transactions = await get_user_transactions(pool, user_id)

    if not transactions:
        if is_callback:
            await message_or_callback.message.edit_text(
                finance_translation["no_transactions"][user_language]
            )
        else:
            await message_or_callback.reply(
                finance_translation["no_transactions"][user_language]
            )
        return

    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_transactions = transactions[start_idx:end_idx]

    history_message = "\n\n".join(
        finance_translation["transaction_row"][user_language].format(
            transaction_id=transaction['transaction_id'],
            amount=transaction['amount'],
            is_closed=finance_translation["yes"][user_language] if transaction['is_closed'] else finance_translation["no"][user_language],
            timestamp=transaction['timestamp']
        )
        for transaction in page_transactions
    )

    keyboard = pagination_keyboard(len(transactions), page, PAGE_SIZE, user_language)

    escaped_history_message = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', history_message)
    escaped_text = finance_translation['history_msg'][user_language].format(history=escaped_history_message)

    if is_callback:
        await message_or_callback.message.edit_text(
            escaped_text, 
            reply_markup=keyboard, 
            parse_mode="MarkdownV2"
        )
        await message_or_callback.answer()
    else:
        await message_or_callback.reply(
            escaped_text, 
            reply_markup=keyboard, 
            parse_mode="MarkdownV2"
        )

async def history_pagination_handler(callback: CallbackQuery, pool):
    """
    Обработка кнопок пагинации для истории транзакций.
    """
    page = int(callback.data.split(":")[1])
    await history_handler(callback, pool, page) 
    await callback.answer()

def extract_user_and_chat_data(message_or_callback):
    """
    Извлекает user_id, chat_id и флаг is_callback из Message или CallbackQuery.
    
    :param message_or_callback: Объект Message или CallbackQuery.
    :return: Кортеж (user_id, chat_id, is_callback).
    """
    if isinstance(message_or_callback, Message):
        return message_or_callback.from_user.id, message_or_callback.chat.id, False
    elif isinstance(message_or_callback, CallbackQuery):
        return message_or_callback.from_user.id, message_or_callback.message.chat.id, True
    else:
        raise ValueError("Unsupported type for message_or_callback")

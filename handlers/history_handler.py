from aiogram.types import Message
from aiogram import Router
from user.transactions import get_user_transactions
from localisation.check_language import check_language
from localisation.translations.finance import translations as finance_translation

router = Router()

async def history_handler(message: Message, pool):
    """
    Обработка кнопки "История" для отображения транзакций пользователя.
    """
    user_id = message.from_user.id
    user_language = await check_language(pool, message.chat.id)

    # Получаем транзакции пользователя
    transactions = await get_user_transactions(pool, user_id)

    if not transactions:
        # Если транзакций нет, отправляем сообщение
        await message.reply(finance_translation["no_transactions"][user_language])
        return

    # Формируем сообщение с историей транзакций
    history_message = "\n".join(
        f"💳 ID: {transaction['transaction_id']}, "
        f"Сумма: {transaction['amount']} ⭐️, "
        f"Закрыта: {'Да' if transaction['is_closed'] else 'Нет'}, "
        f"Время: {transaction['timestamp']}"
        for transaction in transactions
    )

    # Отправляем сообщение с историей транзакций
    await message.reply(
        finance_translation["history_msg"][user_language].format(history=history_message)
    )

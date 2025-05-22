from aiogram.types import LabeledPrice, CallbackQuery
from finance.commission import calculate_final_amount, calculate_commission
from localisation.get_language import get_language
from localisation.translations.finance import translations as finance_translation

async def process_payment(callback: CallbackQuery, amount, provider_token, pool):
    """
    Генерация инвойса для платежа
    """
    user_language = await get_language(pool, callback.message.chat.id)
    prices = [LabeledPrice(label=f"XTR", amount=amount)]
    await callback.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    return dict(
        title=finance_translation["payment_title"][user_language],
        description=finance_translation["payment_description"][user_language].format(amount=amount),
        provider_token=provider_token,
        currency="XTR",
        prices=prices,
        payload=f"user_id:{callback.from_user.id}"
    )

async def handle_successful_payment(pool, user_id, amount):
    """
    Обработка успешной оплаты
    """
    final_amount = calculate_final_amount(amount)
    commission_amount = calculate_commission(amount)

    async with pool.acquire() as connection:
        await connection.execute("""
            INSERT INTO users (user_id, balance) 
            VALUES ($1, 0)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id)

        # Обновляем баланс пользователя
        await connection.execute("""
            UPDATE users 
            SET balance = balance + $1 
            WHERE user_id = $2
        """, final_amount, user_id)

        # Добавляем запись в transaction_for_withdraw
        transaction_id = await connection.fetchval("""
            INSERT INTO transaction_for_withdraw (user_id, amount) 
            VALUES ($1, $2)
            RETURNING id
        """, user_id, final_amount)

        # Добавляем запись в transactions
        await connection.execute("""
            INSERT INTO transactions (transaction_for_withdraw_id, amount) 
            VALUES ($1, $2)
        """, transaction_id, final_amount)

        # Добавляем запись в commission
        await connection.execute("""
            INSERT INTO commission (transaction_id, amount) 
            VALUES ($1, $2)
        """, transaction_id, commission_amount)

    return final_amount

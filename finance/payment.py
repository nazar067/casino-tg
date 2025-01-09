from aiogram.types import LabeledPrice
from finance.commission import calculate_final_amount, calculate_commission

async def process_payment(callback, amount, provider_token):
    """
    Генерация инвойса для платежа
    """
    prices = [LabeledPrice(label=f"XTR", amount=amount)]
    return dict(
        title="Пополнение звёзд",
        description=f"Пополнение на {amount} ⭐️",
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
            INSERT INTO users (user_id, balance) VALUES ($1, 0)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id)
        await connection.execute("""
            UPDATE users SET balance = balance + $1 WHERE user_id = $2
        """, final_amount, user_id)
        transaction_id = await connection.fetchval("""
            INSERT INTO transactions (user_id, amount) VALUES ($1, $2)
            RETURNING id
        """, user_id, final_amount)
        await connection.execute("""
            INSERT INTO commission (transaction_id, amount) VALUES ($1, $2)
        """, transaction_id, commission_amount)

    return final_amount

import asyncpg
from aiogram.types import Message
from aiogram import Dispatcher
from datetime import datetime, timedelta
from finance.check_withdrawable_stars import get_withdrawable_stars
from localisation.translations import translations

async def check_withdrawable_stars(pool, user_id):
    """
    Проверка доступных звёзд для вывода
    """
    async with pool.acquire() as connection:
        cutoff_date = datetime.now() - timedelta(days=21)
        available_stars = await connection.fetchval("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = $1 AND timestamp <= $2
        """, user_id, cutoff_date)

    if available_stars >= 1000:
        return True
    return False

async def process_withdrawal(pool, user_id, amount):
    """
    Обработка вывода звёзд
    """
    async with pool.acquire() as connection:
        cutoff_date = datetime.now() - timedelta(days=21)

        # Получаем доступные транзакции
        transactions = await connection.fetch("""
            SELECT id, amount
            FROM transactions
            WHERE user_id = $1 AND timestamp <= $2
            ORDER BY timestamp ASC
        """, user_id, cutoff_date)

        remaining_to_withdraw = amount
        withdrawals = []

        for transaction in transactions:
            if remaining_to_withdraw <= 0:
                break

            transaction_id = transaction["id"]
            transaction_amount = transaction["amount"]

            amount_to_withdraw = min(transaction_amount, remaining_to_withdraw)

            # Добавляем запись в withdrawals
            await connection.execute("""
                INSERT INTO withdrawals (transaction_id, amount)
                VALUES ($1, $2)
            """, transaction_id, amount_to_withdraw)

            # Обновляем оставшийся баланс транзакции
            await connection.execute("""
                UPDATE transactions
                SET amount = amount - $1
                WHERE id = $2
            """, amount_to_withdraw, transaction_id)

            withdrawals.append((transaction_id, amount_to_withdraw))
            remaining_to_withdraw -= amount_to_withdraw

        withdrawal_details = "\n".join(
            f"Транзакция #{w[0]}: -{w[1]} ⭐️" for w in withdrawals
        )
        return f"Вывод успешно завершён на сумму {amount} ⭐️\nДетали:\n{withdrawal_details}"
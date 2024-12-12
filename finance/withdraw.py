import asyncpg
from aiogram.types import Message
from aiogram import Dispatcher
from datetime import datetime, timedelta
from finance.check_withdrawable_stars import get_withdrawable_stars
from localisation.translations import translations
from finance.transactions import mark_transaction_as_closed

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

async def process_withdrawal(pool, user_id, amount, user_language):
    """
    Обработка вывода звёзд.
    """
    async with pool.acquire() as connection:
        cutoff_date = datetime.now() - timedelta(days=21)

        # Получаем доступные транзакции, которые ещё не закрыты
        transactions = await connection.fetch("""
            SELECT id, amount
            FROM transactions
            WHERE user_id = $1 AND timestamp <= $2 AND is_closed = FALSE
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

            # Добавляем запись в withdrawals и получаем ID вывода
            withdraw_id = await connection.fetchval("""
                INSERT INTO withdrawals (transaction_id, amount)
                VALUES ($1, $2)
                RETURNING id
            """, transaction_id, amount_to_withdraw)

            # Обновляем оставшийся баланс транзакции
            await connection.execute("""
                UPDATE transactions
                SET amount = amount - $1
                WHERE id = $2
            """, amount_to_withdraw, transaction_id)

            # Проверяем остаток транзакции: закрываем только если amount == 0
            remaining_amount = await connection.fetchval("""
                SELECT amount
                FROM transactions
                WHERE id = $1
            """, transaction_id)

            if remaining_amount == 0:
                await mark_transaction_as_closed(pool, transaction_id)

            withdrawals.append((withdraw_id, transaction_id, amount_to_withdraw))
            remaining_to_withdraw -= amount_to_withdraw

        # Обновляем баланс пользователя в таблице `users`
        await connection.execute("""
            UPDATE users
            SET balance = balance - $1
            WHERE user_id = $2
        """, amount, user_id)

        # Формируем детали транзакций
        withdrawal_details = "\n".join(
            translations["withdraw_detail"][user_language].format(
                withdraw_id=w[0], transaction_id=w[1], amount=w[2]
            )
            for w in withdrawals
        )

        # Формируем итоговое сообщение
        return translations["withdraw_success"][user_language].format(
            amount=amount, details=withdrawal_details
        )
        
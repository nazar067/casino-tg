from datetime import datetime, timedelta
from finance.transactions import mark_transaction_as_closed
from localisation.translations.finance import translations as finance_translation

async def check_withdrawable_stars(pool, user_id):
    """
    Проверка доступных звёзд для вывода
    """
    async with pool.acquire() as connection:
        cutoff_date = datetime.now() - timedelta(days=21)
        available_stars = await connection.fetchval("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transaction_for_withdraw
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

        transactions = await connection.fetch("""
            SELECT id, amount
            FROM transaction_for_withdraw
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

            withdraw_id = await connection.fetchval("""
                INSERT INTO withdrawals (transaction_id, amount)
                VALUES ($1, $2)
                RETURNING id
            """, transaction_id, amount_to_withdraw)

            await connection.execute("""
                UPDATE transaction_for_withdraw
                SET amount = amount - $1
                WHERE id = $2
            """, amount_to_withdraw, transaction_id)

            remaining_amount = await connection.fetchval("""
                SELECT amount
                FROM transaction_for_withdraw
                WHERE id = $1
            """, transaction_id)

            if remaining_amount == 0:
                await mark_transaction_as_closed(pool, transaction_id)

            withdrawals.append((withdraw_id, transaction_id, amount_to_withdraw))
            remaining_to_withdraw -= amount_to_withdraw

        await connection.execute("""
            UPDATE users
            SET balance = balance - $1
            WHERE user_id = $2
        """, amount, user_id)

        withdrawal_details = "\n".join(
            finance_translation["withdraw_detail"][user_language].format(
                withdraw_id=w[0], transaction_id=w[1], amount=w[2]
            )
            for w in withdrawals
        )

        return finance_translation["withdraw_success"][user_language].format(
            amount=amount, details=withdrawal_details
        )
        
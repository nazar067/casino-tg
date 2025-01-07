from datetime import datetime

async def account_addition(pool, user_id: int, amount: int):
    """
    Добавление средств на баланс пользователя и запись в таблицу transactions.
    """
    async with pool.acquire() as connection:
        await connection.execute("""
            INSERT INTO users (user_id, balance)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE
            SET balance = users.balance + $2
        """, user_id, amount)

        await connection.execute("""
            INSERT INTO transactions (user_id, amount, is_closed, timestamp)
            VALUES ($1, $2, FALSE, $3)
        """, user_id, amount, datetime.now())

async def account_withdrawal(pool, user_id: int, withdrawal_amount: int):
    """
    Снятие средств с баланса пользователя и из таблицы transactions.
    """
    async with pool.acquire() as connection:
        current_balance = await connection.fetchval("""
            SELECT balance FROM users WHERE user_id = $1
        """, user_id)

        if not current_balance or current_balance < withdrawal_amount:
            raise ValueError("Недостаточно средств на балансе.")

        await connection.execute("""
            UPDATE users
            SET balance = balance - $1
            WHERE user_id = $2
        """, withdrawal_amount, user_id)

        remaining_to_withdraw = withdrawal_amount

        while remaining_to_withdraw > 0:
            transaction = await connection.fetchrow("""
                SELECT id, amount
                FROM transactions
                WHERE user_id = $1 AND is_closed = FALSE
                ORDER BY timestamp ASC
                LIMIT 1
            """, user_id)

            if not transaction:
                raise ValueError("Не удалось найти доступные транзакции для снятия.")

            transaction_id = transaction["id"]
            transaction_amount = transaction["amount"]

            amount_to_withdraw = min(transaction_amount, remaining_to_withdraw)

            # Обновляем сумму транзакции
            await connection.execute("""
                UPDATE transactions
                SET amount = amount - $1
                WHERE id = $2
            """, amount_to_withdraw, transaction_id)

            # Закрываем транзакцию, если её сумма стала равна 0
            await connection.execute("""
                UPDATE transactions
                SET is_closed = TRUE
                WHERE id = $1 AND amount = 0
            """, transaction_id)

            remaining_to_withdraw -= amount_to_withdraw

from datetime import datetime

async def account_addition(pool, user_id: int, amount: int):
    """
    Добавление средств на баланс пользователя и запись в таблицы transaction_for_withdraw и transactions.
    """
    async with pool.acquire() as connection:
        await connection.execute("""
            INSERT INTO users (user_id, balance)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE
            SET balance = users.balance + $2
        """, user_id, amount)

        transaction_id = await connection.fetchval("""
            INSERT INTO transaction_for_withdraw (user_id, amount, is_closed, timestamp)
            VALUES ($1, $2, FALSE, $3)
            RETURNING id
        """, user_id, amount, datetime.now())

        await connection.execute("""
            INSERT INTO transactions (transaction_for_withdraw_id, amount)
            VALUES ($1, $2)
        """, transaction_id, amount)


async def account_withdrawal(pool, user_id: int, updated_balance: int):
    """
    Обновление средств на баланса пользователя.
    """
    async with pool.acquire() as connection:
        await connection.execute("""
            UPDATE users
            SET balance = $1
            WHERE user_id = $2
        """, updated_balance, user_id)
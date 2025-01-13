from typing import List, Dict
from asyncpg import Pool

async def get_user_transactions(pool: Pool, user_id: int) -> List[Dict]:
    """
    Извлекает все транзакции пользователя из таблиц transactions и transaction_for_withdraw.

    :param pool: Подключение к базе данных (asyncpg pool).
    :param user_id: Идентификатор пользователя.
    :return: Список словарей с данными о транзакциях.
    """
    async with pool.acquire() as connection:
        transactions = await connection.fetch("""
            SELECT 
                t.transaction_id,
                t.amount AS transaction_amount,
                tfw.timestamp AS transaction_timestamp,
                tfw.is_closed
            FROM transactions t
            JOIN transaction_for_withdraw tfw
            ON t.transaction_id = tfw.id
            WHERE tfw.user_id = $1
            ORDER BY tfw.timestamp DESC
        """, user_id)

    # Форматируем timestamp в человекочитаемый вид
    result = [
        {
            "transaction_id": record["transaction_id"],
            "amount": record["transaction_amount"],
            "timestamp": record["transaction_timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "is_closed": record["is_closed"]
        }
        for record in transactions
    ]
    return result

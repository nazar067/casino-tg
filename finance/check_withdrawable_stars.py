import asyncpg
from datetime import datetime, timedelta

async def get_withdrawable_stars(pool: asyncpg.pool.Pool, user_id: int) -> int:
    """
    Проверяет, сколько звёзд доступно для вывода у пользователя.

    :param pool: Пул подключений к базе данных.
    :param user_id: Идентификатор пользователя.
    :return: Количество звёзд, доступных для вывода.
    """
    async with pool.acquire() as connection:
        # Рассчитываем дату, старше которой должны быть транзакции
        cutoff_date = datetime.now() - timedelta(days=21)

        # Суммируем звёзды из транзакций, удовлетворяющих условиям
        result = await connection.fetchval("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = $1 AND timestamp <= $2
        """, user_id, cutoff_date)

    # Возвращаем сумму доступных звёзд
    return result or 0

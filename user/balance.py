async def get_user_balance(pool, user_id):
    """
    Получение баланса пользователя
    """
    async with pool.acquire() as connection:
        balance = await connection.fetchval("""
            SELECT balance FROM users WHERE user_id = $1
        """, user_id)
    return balance or 0

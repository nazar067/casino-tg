async def has_active_game(pool, user_id):
    """
    Проверяет, есть ли у пользователя активная игра.
    """
    async with pool.acquire() as connection:
        active_game = await connection.fetchrow("""
            SELECT id FROM gameDice
            WHERE (player1_id = $1 OR player2_id = $1) AND is_closed = FALSE
        """, user_id)
        return active_game is not None
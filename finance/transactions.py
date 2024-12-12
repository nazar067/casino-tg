async def mark_transaction_as_closed(pool, transaction_id):
    """
    Помечает транзакцию как закрытую.
    """
    async with pool.acquire() as connection:
        await connection.execute("""
            UPDATE transactions
            SET is_closed = TRUE
            WHERE id = $1
        """, transaction_id)

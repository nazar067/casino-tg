import asyncpg

async def get_db_pool(database_url):
    """
    Создание пула соединений с базой данных
    """
    return await asyncpg.create_pool(database_url)

async def init_db(pool):
    """
    Инициализация базы данных: создание таблиц
    """
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                balance INT DEFAULT 0
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                amount INT NOT NULL,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)

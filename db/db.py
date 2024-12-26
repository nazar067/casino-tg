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
                is_closed BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id SERIAL PRIMARY KEY,
                transaction_id INT NOT NULL REFERENCES transactions(id),
                amount INT NOT NULL,
                is_closed BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS languages (
                chat_id BIGINT PRIMARY KEY,
                language_code TEXT NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS gameDice (
                id SERIAL PRIMARY KEY,
                player1_id BIGINT NOT NULL,
                player2_id BIGINT,
                winner_id BIGINT,
                bet INT NOT NULL,
                is_closed BOOLEAN DEFAULT FALSE
            )
        """)


from finance.account import account_addition, account_withdrawal


async def process_game_result(pool, game_id):
    """
    Общий функционал для обработки результата игры.
    """
    async with pool.acquire() as connection:
        game = await connection.fetchrow("""
            SELECT player1_id, player2_id, number1, number2, bet
            FROM game_dice
            WHERE id = $1
        """, game_id)

        if not game or game["number1"] is None or game["number2"] is None:
            return None, None, None, None, None

        bet = game["bet"]
        player1_id = game["player1_id"]
        player2_id = game["player2_id"]
        number1 = game["number1"]
        number2 = game["number2"]

        if number1 > number2:
            winner_id = player1_id
            loser_id = player2_id
        elif number1 < number2:
            winner_id = player2_id
            loser_id = player1_id
        else:
            winner_id = None
            loser_id = None

        if winner_id and loser_id:
            await account_withdrawal(pool, loser_id, bet)
            await account_addition(pool, winner_id, bet)

        await connection.execute("""
            UPDATE game_dice
            SET winner_id = $1, is_closed = TRUE
            WHERE id = $2
        """, winner_id, game_id)

        return player1_id, player2_id, winner_id, loser_id, bet
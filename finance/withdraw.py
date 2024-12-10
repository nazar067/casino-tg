from finance.check_withdrawable_stars import get_withdrawable_stars

async def check_withdrawable_stars(pool, user_id):
    available_stars = await get_withdrawable_stars(pool, user_id)

    if available_stars >= 1000:
        return f"Доступно для вывода: {available_stars} звёзд ⭐️"
    else:
        return f"Недостаточно звёзд для вывода. Доступно: {available_stars} ⭐️, нужно минимум 1000 ⭐️."

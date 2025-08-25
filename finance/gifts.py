from typing import Dict, List, Optional
from aiogram import Bot
import json

async def get_available_gifts(bot: Bot):
    """
    Получение доступных подарков от бота.
    """
    avaliable_gifts_json = await bot.get_available_gifts()
    return [{"id": str(g.id), "star_count": int(g.star_count)} for g in avaliable_gifts_json.gifts]

async def select_gifts(gifts: List[Dict[str, int]], amount: int) -> Optional[List[str]]:
    """
    Подбирает комбинацию подарков, сумма star_count которых равна amount.
    Возвращает список id или None, если точной комбинации нет.
    """
    gifts_sorted = sorted(gifts, key=lambda g: g["star_count"], reverse=True)
    result = []
    total = 0

    for gift in gifts_sorted:
        while total + gift["star_count"] <= amount:
            result.append(gift["id"])
            total += gift["star_count"]
            if total == amount:
                return result

    return None

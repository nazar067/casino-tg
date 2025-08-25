import asyncio
from aiogram import Bot
from datetime import datetime, timedelta
from finance.account import account_withdrawal
from finance.gifts import get_available_gifts, select_gifts
from localisation.translations.finance import translations as finance_translation
from user.balance import get_user_balance

async def process_withdrawal(bot: Bot, pool, user_id, amount, user_language):
    """
    Обработка вывода звёзд.
    """
    user_balance = await get_user_balance(pool, user_id)
    if(user_balance < amount):
        await bot.send_message(
            chat_id=user_id,
            text=finance_translation["withdraw_unavailable"][user_language]
        )
        return
    
    gifts = await get_available_gifts(bot)
    gifts_for_withdrawal = await select_gifts(gifts, amount)
    
    if gifts_for_withdrawal is None:
        await bot.send_message(
            chat_id=user_id,
            text=finance_translation["withdraw_no_exact_gift_combination"][user_language]
        )
        return
    
    updated_user_balance = user_balance - amount
    await account_withdrawal(pool, user_id, updated_user_balance)
    
    for gift in gifts_for_withdrawal:
        await bot.send_gift(user_id, gift)
        await asyncio.sleep(1)
    
    
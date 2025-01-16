from aiogram.types import Message
from aiogram import Router
from datetime import datetime

from admin.check_is_admin import is_user_admin
from localisation.check_language import check_language
from localisation.translations.finance import translations as finance_translation

router = Router()
commission_rate = 0.02

async def commission_withdraw_handler(message: Message, pool):
    user_id = message.from_user.id
    user_language = await check_language(pool, message.chat.id)
    if not is_user_admin(user_id):
        return
    
    amount = int(message.text.split(maxsplit=1)[1])
    if amount <= 0:
        raise ValueError

    async with pool.acquire() as connection:
        await connection.execute("""
            INSERT INTO commission_withdraw (amount, timestamp)
            VALUES ($1, $2)
        """, amount, datetime.now())

    await message.reply(finance_translation["success_commission_withdraw"][user_language].format(amount=amount))

async def variance_handler(message: Message, pool):
    user_id = message.from_user.id
    user_language = await check_language(pool, message.chat.id)
    
    if not is_user_admin(user_id):
        return
    
    async with pool.acquire() as connection:
        commission_total = await connection.fetchval("""
            SELECT COALESCE(SUM(amount), 0)
            FROM commission
        """)

        commission_withdraw_total = await connection.fetchval("""
            SELECT COALESCE(SUM(amount), 0)
            FROM commission_withdraw
        """)

    variance = commission_total - commission_withdraw_total

    message_text = finance_translation["variance_msg"][user_language].format(
        commission_total=commission_total,
        commission_withdraw_total=commission_withdraw_total,
        variance=variance
    )

    await message.reply(message_text)

def calculate_final_amount(amount: int) -> int:
    """
    Расчет окончательной суммы с учетом комиссии
    """
    commission = calculate_commission(amount)
    return max(amount - commission, 0)

def calculate_commission(amount: int) -> int:
    """
    Расчет комиссии
    """
    if amount < 100:
        return 2
    return int(amount * commission_rate)

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery
from aiogram.filters import Command
from config import API_TOKEN
from finance.payment import process_payment, handle_successful_payment
from user.balance import get_user_balance
from finance.keyboards import payment_keyboard

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    """
    Команда /start
    """
    await message.answer("👋 Добро пожаловать в наш бот! Здесь вы можете поддерживать проект звездами ⭐️.")


@router.message(Command("donate"))
async def donate_handler(message: Message):
    """
    Команда /donate для пополнения
    """
    # Используем клавиатуру из keyboards.py
    await message.answer("Выберите сумму для пополнения:", reply_markup=payment_keyboard())


@router.callback_query(lambda c: c.data.startswith("pay:"))
async def pay_stars_handler(callback: CallbackQuery):
    """
    Обработка платежей с валютой XTR
    """
    amount = int(callback.data.split(":")[1])  # Получаем сумму из callback data
    provider_token = ""

    # Генерация инвойса
    payment_data = await process_payment(callback, amount, provider_token)
    if payment_data:
        await callback.message.answer_invoice(**payment_data)        

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """
    Обработка PreCheckoutQuery
    """
    await pre_checkout_query.answer(ok=True)  # Подтверждаем предчекаут

@router.message(lambda m: m.successful_payment)
async def successful_payment_handler(message: Message):
    """
    Обработка успешной оплаты
    """
    user_id = message.from_user.id
    amount = message.successful_payment.total_amount  # Конвертируем из копеек в целое число
    pool = dp["db_pool"]

    # Обрабатываем успешную оплату через handle_successful_payment
    final_amount = await handle_successful_payment(pool, user_id, amount)

    await message.answer(f"✅ Баланс успешно пополнен на {final_amount} ⭐️!")

@router.message(Command("balance"))
async def balance_handler(message: Message):
    """
    Команда /balance для проверки баланса
    """
    pool = dp["db_pool"]
    user_id = message.from_user.id
    balance = await get_user_balance(pool, user_id)
    await message.answer(f"💰 Ваш текущий баланс: {balance} ⭐️")


async def main():
    """
    Запуск бота
    """
    # Подключение базы данных и роутера
    pool = await get_db_pool(DATABASE_URL)
    dp["db_pool"] = pool
    await init_db(pool)
    dp.include_router(router)

    try:
        print("Бот запущен!")
        await dp.start_polling(bot)
    finally:
        await pool.close()
        await bot.session.close()


if __name__ == "__main__":
    import asyncio
    from config import DATABASE_URL
    from db.db import get_db_pool, init_db
    asyncio.run(main())

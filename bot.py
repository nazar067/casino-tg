from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from config import API_TOKEN
from finance.payment import process_payment, handle_successful_payment
from handlers.balance_handler import balance_handler
from handlers.donate_handler import donate_handler
from handlers.withdraw_handler import withdraw_handler
from user.balance import get_user_balance
from keyboards.keyboard import menu_keyboard, payment_keyboard
from localisation.translations import translations
from localisation.get_language import get_language
from localisation.check_language import check_language
from handlers.withdraw_handler import router as withdraw_router

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(withdraw_router)
router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    """
    Команда /start
    """
    pool = dp["db_pool"]
    chat_id = message.chat.id
    language_code = message.from_user.language_code

    await get_language(pool, chat_id, language_code)

    user_language = await check_language(pool, chat_id)

    await message.reply(
        translations["welcome"][user_language],
        reply_markup=menu_keyboard(user_language) 
    )

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
    
@router.message()
async def button_handler(message: Message, state: FSMContext):
    """
    Обработка всех кнопок на основе локализации
    """
    pool = dp["db_pool"]
    user_language = await check_language(pool, message.chat.id)

    if message.text == translations["balance_btn"][user_language]:
        await message.answer(await balance_handler(message, dp, user_language))
    elif message.text == translations["donate"][user_language]:
        text, keyboard = await donate_handler(message, dp, user_language)
        await message.answer(text, reply_markup=keyboard)
    elif message.text == translations["withdraw_btn"][user_language]:
        await withdraw_handler(message, dp, user_language, state)

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

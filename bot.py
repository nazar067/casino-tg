from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery
from aiogram.filters import Command
from telegram import ReplyKeyboardMarkup
from config import API_TOKEN
from finance.payment import process_payment, handle_successful_payment
from user.balance import get_user_balance
from keyboards.keyboard import menu_keyboard, payment_keyboard
from localisation.translations import translations
from localisation.get_language import get_language
from localisation.check_language import check_language

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
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

@router.message(Command("donate"))
async def donate_handler(message: Message):
    """
    Команда /donate для пополнения
    """
    pool = dp["db_pool"]
    chat_id = message.chat.id

    # Проверяем текущий язык
    user_language = await check_language(pool, chat_id)

    # Отправляем сообщение с InlineKeyboardMarkup
    await message.answer(
        "Выберите сумму для пополнения:",
        reply_markup=payment_keyboard(user_language)
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

@router.message(Command("balance"))
async def balance_handler(message: Message):
    """
    Команда /balance
    """
    pool = dp["db_pool"]
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    balance = await get_user_balance(pool, user_id)
    
    user_language = await check_language(pool, chat_id)
    
    await message.answer(translations["balance"][user_language].format(balance=balance))

@router.message(lambda m: m.text in ["Пополнить", "Withdraw", "Поповнити"])
async def donate_button_handler(message: Message):
    """
    Обработка кнопки "Пополнить" из меню
    """
    pool = dp["db_pool"]
    chat_id = message.chat.id

    # Проверяем текущий язык пользователя
    user_language = await check_language(pool, chat_id)

    # Отправляем локализованную клавиатуру для пополнения
    await message.answer(
        translations["welcome"][user_language],
        reply_markup=payment_keyboard(user_language)
    )

@router.message(lambda m: m.text in ["Вывести", "Withdraw", "Вивести"])
async def withdraw_handler(message: Message):
    """
    Обработка кнопки "Вывести" из меню
    """
    pool = dp["db_pool"]
    chat_id = message.chat.id

    # Проверяем текущий язык пользователя
    user_language = await check_language(pool, chat_id)

    # Отправляем локализованное сообщение
    await message.answer(translations["withdraw"][user_language])

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

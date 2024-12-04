import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from aiogram.filters import Command
from aiogram import F
from config import TELEGRAM_API_TOKEN, PROVIDER_TOKEN
from finance.keyboards import payment_keyboard

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher()

# Хендлер для отправки инвойса
async def send_invoice_handler(message: Message):  
    prices = [LabeledPrice(label="XTR", amount=10)]  
    await message.answer_invoice(  
        title="Поддержка канала",  
        description="Поддержать канал на 10 звёзд!",  
        prices=prices,  
        provider_token="",  
        payload="channel_support",  
        currency="XTR",  
        reply_markup=payment_keyboard(),  
    )

# Хендлер для предчекаут-обработки
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

# Хендлер успешного платежа
async def success_payment_handler(message: Message):
    await message.answer(text="🥳 Спасибо за вашу поддержку! 🤗")

# Хендлер сообщения о поддержке
async def pay_support_handler(message: Message):
    await message.answer(
        text="Добровольные пожертвования не подразумевают возврат средств, "
        "однако, если вы очень хотите вернуть средства - свяжитесь с нами."
    )

# Регистрация хендлеров
dp.message.register(send_invoice_handler, Command(commands="donate"))
dp.pre_checkout_query.register(pre_checkout_handler)
dp.message.register(success_payment_handler, F.successful_payment)
dp.message.register(pay_support_handler, Command(commands="paysupport"))

# Запуск бота
async def main():
    try:
        print("Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

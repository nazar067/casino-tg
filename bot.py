import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from finance.payment import get_paypal_access_token, create_payment
from finance.withdrawal import get_paypal_access_token as get_withdrawal_token, create_payout
from config import TELEGRAM_API_TOKEN

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher()

# Кнопки для взаимодействия
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Оплатить"), KeyboardButton(text="Запросить возврат")]
    ],
    resize_keyboard=True
)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """
    Команда /start
    """
    await message.answer(
        "Привет! Я бот для работы с PayPal. Вы можете оплатить или запросить возврат.",
        reply_markup=keyboard,
    )


@dp.message(lambda msg: msg.text == "Оплатить")
async def handle_payment_request(message: Message):
    """
    Обработка запроса на оплату
    """
    try:
        access_token = get_paypal_access_token()
        payment_response = create_payment(
            access_token=access_token,
            amount="10.00",
            currency="USD",
        )
        approval_url = next(link["href"] for link in payment_response["links"] if link["rel"] == "approval_url")
        await message.answer(f"Для оплаты перейдите по ссылке: {approval_url}")
    except Exception as e:
        await message.answer(f"Ошибка при создании платежа: {e}")


@dp.message(lambda msg: msg.text == "Запросить возврат")
async def handle_refund_request(message: Message):
    """
    Обработка запроса на возврат
    """
    user_email = "receiver@example.com"  # Почта пользователя в PayPal
    amount = "10.00"  # Сумма возврата
    try:
        access_token = get_withdrawal_token()
        payout_response = create_payout(access_token, user_email, amount)
        await message.answer(f"Выплата успешно отправлена: {payout_response}")
    except Exception as e:
        await message.answer(f"Ошибка при выполнении выплаты: {e}")


async def main():
    """
    Основная функция запуска бота
    """
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

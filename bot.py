from logs.write_server_errors import setup_logging
setup_logging()

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from config import API_TOKEN
from privacy.privacy import get_privacy
from bot_settings.commands import set_bot_commands
from bot_settings.description import set_bot_description
from bot_settings.short_description import set_bot_short_description
from finance.payment import process_payment, handle_successful_payment
from keyboards.keyboard import language_keyboard
from logs.send_server_errors import send_server_logs
from handlers.language_handler import set_language_handler
from games.dice.register_game import create_game_handler
from handlers.balance_handler import balance_handler
from handlers.donate_handler import donate_handler
from handlers.history_handler import history_handler
from handlers.withdraw_handler import withdraw_handler
from localisation.get_language import get_language
from handlers.start_handler import start_handler
from handlers.withdraw_handler import router as withdraw_router
from games.dice.join_game import join_game_handler, router as join_game_router
from games.dice.cancel_game import cancel_game_handler, periodic_cleanup, router as cancel_game_router
from games.dice.process_game import handle_dice_roll, router as process_game_router
from handlers.history_handler import history_pagination_handler, router as history_router
from finance.commission import commission_withdraw_handler, variance_handler
from localisation.translations.finance import translations as finance_translation
from localisation.translations.general import translations as general_translation

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(withdraw_router)
dp.include_router(join_game_router)
dp.include_router(cancel_game_router)
dp.include_router(process_game_router)
dp.include_router(history_router)
router = Router()

@router.message(Command(commands=["start"]))
async def start(message: Message):
    """
    Команда /start
    """
    await start_handler(message, dp)
    
@router.message(Command(commands=["dice"]))
async def dice_handler(message: Message, state: FSMContext):
    """
    Команда /dice для создания игры в кости.
    """
    pool = dp["db_pool"]
    await create_game_handler(message, pool, state)
    
@router.message(Command(commands=["serverLogs"]))
async def server_logs(message: Message):
    """
    Отправка файла serverLogs после проверки прав пользователя.
    """
    await send_server_logs(message, dp)
    
@router.message(Command(commands=["commissionWithdraw"]))
async def commission_command_handler(message: Message):
    """
    Обработка команды /commissionWithdraw.
    """
    pool = dp["db_pool"]
    await commission_withdraw_handler(message, pool)
    
@router.message(Command(commands=["variance"]))
async def variance_command_handler(message: Message):
    """
    Обработка команды /variance.
    """
    pool = dp["db_pool"]
    await variance_handler(message, pool)
    
@router.message(Command(commands=["changelang"]))
async def change_language_handler(message: Message):
    """
    Обработка команды /changelang. Показывает кнопки выбора языка.
    """
    pool = dp["db_pool"]
    user_language = await get_language(pool, message.chat.id)
    await message.reply(
        general_translation["choose_lang"][user_language],
        reply_markup=language_keyboard()
    )
    
@router.message(Command(commands=["privacy"]))
async def privacy_handler(message: Message):
    """
    Обработка команды /privacy.
    """
    await get_privacy(message, dp)

@router.callback_query(lambda callback: callback.data.startswith("join_game:"))
async def join_dice_handler(callback: CallbackQuery):
    """
    Обработка нажатия кнопки для присоединения к игре.
    """
    pool = dp["db_pool"]
    await join_game_handler(callback, pool)
    
@router.callback_query(lambda callback: callback.data.startswith("set_language:"))
async def language_handler(callback: CallbackQuery):
    """
    Обработка нажатия кнопки для присоединения к игре.
    """
    pool = dp["db_pool"]
    await set_language_handler(callback, pool)

@router.callback_query(lambda callback: callback.data.startswith("cancel_game:"))
async def cancel_dice_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обработка нажатия кнопки для отмены игры.
    """
    pool = dp["db_pool"]
    await cancel_game_handler(callback, pool, state)
    
@router.callback_query(lambda callback: callback.data.startswith("history_page:"))
async def history_user_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обработка нажатия кнопки для отмены игры.
    """
    pool = dp["db_pool"]
    await history_pagination_handler(callback, pool)

@router.message(lambda message: message.dice and not message.forward_date)
async def dice_roll_handler(message: Message):
    """
    Обработка броска кубика игроками.
    """
    pool = dp["db_pool"]
    await handle_dice_roll(pool, message)

@router.callback_query(lambda c: c.data.startswith("pay:"))
async def pay_stars_handler(callback: CallbackQuery):
    """
    Обработка платежей с валютой XTR
    """
    amount = int(callback.data.split(":")[1])
    provider_token = ""

    pool = dp["db_pool"]
    payment_data = await process_payment(callback, amount, provider_token, pool)
    if payment_data:
        await callback.message.answer_invoice(**payment_data)        

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """
    Обработка PreCheckoutQuery
    """
    await pre_checkout_query.answer(ok=True)

@router.message(lambda m: m.successful_payment)
async def successful_payment_handler(message: Message):
    """
    Обработка успешной оплаты
    """
    user_id = message.from_user.id
    amount = message.successful_payment.total_amount
    pool = dp["db_pool"]
    user_language = await get_language(pool, message.chat.id)

    final_amount = await handle_successful_payment(pool, user_id, amount)

    await message.answer(finance_translation["donate_success"][user_language].format(final_amount=final_amount))
    
@router.message()
async def button_handler(message: Message, state: FSMContext):
    """
    Обработка всех кнопок на основе локализации
    """
    pool = dp["db_pool"]
    user_language = await get_language(pool, message.chat.id)

    if message.text == finance_translation["balance_btn"][user_language]:
        await message.reply(await balance_handler(message, dp, user_language))
    elif message.text == finance_translation["donate"][user_language]:
        text, keyboard = await donate_handler(message, dp, user_language)
        await message.reply(text, reply_markup=keyboard)
    elif message.text == finance_translation["withdraw_btn"][user_language]:
        await withdraw_handler(message, dp, user_language, state)
    elif message.text == finance_translation["history_btn"][user_language]:
        await history_handler(message, pool)

async def main():
    """
    Запуск бота
    """
    pool = await get_db_pool(DATABASE_URL)
    dp["db_pool"] = pool
    await init_db(pool)
    dp.include_router(router)
    
    await set_bot_description(bot)
    await set_bot_commands(bot)
    await set_bot_short_description(bot)
    
    asyncio.create_task(periodic_cleanup(pool, bot))

    try:
        print("Bot started")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "pre_checkout_query"])
    finally:
        await pool.close()
        await bot.session.close()

if __name__ == "__main__":
    import asyncio
    from config import DATABASE_URL
    from db.db import get_db_pool, init_db
    asyncio.run(main())

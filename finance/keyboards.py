from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Кнопки для выбора суммы оплаты
    for amount in [3, 50, 100, 200, 500]:
        builder.button(text=f"Пополнить на {amount} ⭐️", callback_data=f"pay:{amount}")
    
    return builder.as_markup()

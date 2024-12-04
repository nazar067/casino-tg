from aiogram.utils.keyboard import InlineKeyboardBuilder

def payment_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплатить 20 ⭐️", pay=True)
    return builder.as_markup()

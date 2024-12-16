from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from localisation.translations import translations

amounts = [3, 50, 100, 200, 500, 1000] 

def payment_keyboard(language: str) -> InlineKeyboardMarkup:
    """
    Создание клавиатуры с кнопками оплаты, локализованной по языку.
    """
    builder = InlineKeyboardBuilder()
    text = translations['donate'][language][2:-2]

    # Кнопки для выбора суммы оплаты
    for amount in [3, 50, 100, 200, 500, 1000]:
        builder.button(
            text=f"{text} на {amount} ⭐️",
            callback_data=f"pay:{amount}"
        )
    builder.adjust(2)  # Расположить кнопки по две в ряд

    return builder.as_markup()

def menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    """
    Создание меню с кнопками "Пополнить" и "Вывести", локализованного по языку.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=translations["donate"][language]),  # Кнопка "Пополнить"
                KeyboardButton(text=translations["withdraw_btn"][language]),  # Кнопка "Вывести"
            ],
            [
                KeyboardButton(text=translations["balance_btn"][language])  # Кнопка "Баланс" на отдельной строке
            ]
        ],
        resize_keyboard=True,  # Клавиатура будет адаптироваться под экран
    )
    
def cancel_keyboard(language: str) -> InlineKeyboardMarkup:
    """
    Создание клавиатуры с кнопкой "Отмена".
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=translations["cancel_btn"][language],
        callback_data="cancel_withdraw"
    )
    return builder.as_markup()
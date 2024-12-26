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

    for amount in amounts:
        builder.button(
            text=f"{text} на {amount} ⭐️",
            callback_data=f"pay:{amount}"
        )
    builder.adjust(2)

    return builder.as_markup()

def menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    """
    Создание меню с кнопками "Пополнить" и "Вывести", локализованного по языку.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=translations["donate"][language]),
                KeyboardButton(text=translations["withdraw_btn"][language]),
            ],
            [
                KeyboardButton(text=translations["balance_btn"][language])
            ]
        ],
        resize_keyboard=True,
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

def join_dice_button(game_id: int, bet: int, language: str) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру с кнопкой для присоединения к игре.
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=translations["join_dice_btn"][language].format(bet=bet),
        callback_data="join_game:" + str(game_id)
    )
    return builder.as_markup()

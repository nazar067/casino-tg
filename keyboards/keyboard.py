from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from localisation.translations.finance import translations as finance_translation
from localisation.translations.dice import translations as dice_translation

amounts = [3, 50, 100, 200, 500, 1000] 

def payment_keyboard(language: str) -> InlineKeyboardMarkup:
    """
    Создание клавиатуры с кнопками оплаты, локализованной по языку.
    """
    builder = InlineKeyboardBuilder()
    text = finance_translation['donate'][language][2:-2]

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
                KeyboardButton(text=finance_translation["donate"][language]),
                KeyboardButton(text=finance_translation["withdraw_btn"][language]),
            ],
            [
                KeyboardButton(text=finance_translation["balance_btn"][language])
            ]
        ],
        resize_keyboard=True,
    )
    
def game_buttons(game_id: int, bet: int, language: str) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру с кнопками для игры (Присоединиться и Отмена).
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=dice_translation["cancel_btn"][language],
                    callback_data=f"cancel_game:{game_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=dice_translation["join_dice_btn"][language].format(bet=bet),
                    callback_data=f"join_game:{game_id}"
                )
            ]
        ]
    )
    
def cancel_keyboard(language: str) -> InlineKeyboardMarkup:
    """
    Создание клавиатуры с кнопкой "Отмена".
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=finance_translation["cancel_btn"][language],
        callback_data="cancel_withdraw"
    )
    return builder.as_markup()

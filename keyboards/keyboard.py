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
    Создание меню с кнопками "Пополнить", "Вывести", "Баланс" и "История".
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=finance_translation["donate"][language]),
                KeyboardButton(text=finance_translation["withdraw_btn"][language]),
            ],
            [
                KeyboardButton(text=finance_translation["balance_btn"][language]),
                KeyboardButton(text=finance_translation["history_btn"][language])
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

def pagination_keyboard(total_items: int, current_page: int, page_size: int, language: str) -> InlineKeyboardMarkup:
    """
    Создание кнопок пагинации для истории транзакций.

    :param total_items: Общее количество элементов.
    :param current_page: Текущая страница.
    :param page_size: Количество элементов на странице.
    :param language: Язык пользователя.
    :return: Клавиатура с кнопками пагинации.
    """
    total_pages = (total_items + page_size - 1) // page_size
    builder = InlineKeyboardBuilder()

    if current_page > 1:
        builder.button(
            text=finance_translation["prev_page_btn"][language],
            callback_data=f"history_page:{current_page - 1}"
        )

    if current_page < total_pages:
        builder.button(
            text=finance_translation["next_page_btn"][language],
            callback_data=f"history_page:{current_page + 1}"
        )

    builder.adjust(2)
    return builder.as_markup()


def language_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для смены языка.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="English", callback_data="set_language:en")
    builder.button(text="Русский", callback_data="set_language:ru")
    builder.button(text="Українська", callback_data="set_language:uk")
    builder.adjust(1)
    return builder.as_markup()

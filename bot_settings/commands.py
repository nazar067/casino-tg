from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeAllGroupChats
from localisation.translations.bot import translations as bot_translation

async def set_bot_commands(bot: Bot):
    """
    Устанавливает список команд бота с описаниями.
    """
    private_commands_en = [
        BotCommand(command="start", description=bot_translation["start_command_desc"]["en"]),
        BotCommand(command="dice", description=bot_translation["dice_command_desc"]["en"]),
        BotCommand(command="privacy", description=bot_translation["privacy_command_desc"]["en"]),
        BotCommand(command="changelang", description=bot_translation["changelang_command_desc"]["en"]),
    ]
    private_commands_uk = [
        BotCommand(command="start", description=bot_translation["start_command_desc"]["uk"]),
        BotCommand(command="dice", description=bot_translation["dice_command_desc"]["uk"]),
        BotCommand(command="privacy", description=bot_translation["privacy_command_desc"]["uk"]),
        BotCommand(command="changelang", description=bot_translation["changelang_command_desc"]["uk"]),
    ]
    private_commands_ru = [
        BotCommand(command="start", description=bot_translation["start_command_desc"]["ru"]),
        BotCommand(command="dice", description=bot_translation["dice_command_desc"]["ru"]),
        BotCommand(command="privacy", description=bot_translation["privacy_command_desc"]["ru"]),
        BotCommand(command="changelang", description=bot_translation["changelang_command_desc"]["ru"]),
    ]
    
    group_commands_en = [
        BotCommand(command="start", description=bot_translation["start_command_desc_group"]["en"]),
        BotCommand(command="dice", description=bot_translation["dice_command_desc"]["en"]),
        BotCommand(command="privacy", description=bot_translation["privacy_command_desc"]["en"]),
        BotCommand(command="changelang", description=bot_translation["changelang_command_desc"]["en"]),
    ]
    group_commands_uk = [
        BotCommand(command="start", description=bot_translation["start_command_desc_group"]["uk"]),
        BotCommand(command="dice", description=bot_translation["dice_command_desc"]["uk"]),
        BotCommand(command="privacy", description=bot_translation["privacy_command_desc"]["uk"]),
        BotCommand(command="changelang", description=bot_translation["changelang_command_desc"]["uk"]),
    ]
    group_commands_ru = [
        BotCommand(command="start", description=bot_translation["start_command_desc_group"]["ru"]),
        BotCommand(command="dice", description=bot_translation["dice_command_desc"]["ru"]),
        BotCommand(command="privacy", description=bot_translation["privacy_command_desc"]["ru"]),
        BotCommand(command="changelang", description=bot_translation["changelang_command_desc"]["ru"]),
    ]

    await bot.set_my_commands(commands=private_commands_en, scope=BotCommandScopeDefault(), language_code="en")
    await bot.set_my_commands(commands=private_commands_uk, scope=BotCommandScopeDefault(), language_code="uk")
    await bot.set_my_commands(commands=private_commands_ru, scope=BotCommandScopeDefault(), language_code="ru")
    
    await bot.set_my_commands(commands=group_commands_en, scope=BotCommandScopeAllGroupChats(), language_code="en")
    await bot.set_my_commands(commands=group_commands_uk, scope=BotCommandScopeAllGroupChats(), language_code="uk")
    await bot.set_my_commands(commands=group_commands_ru, scope=BotCommandScopeAllGroupChats(), language_code="ru")

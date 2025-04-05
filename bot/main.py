from telebot import TeleBot
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bot.config import Config
from bot.handlers.help import setup_help_handlers
from bot.database import create_db_connection
from bot.handlers.callbacks import setup_callbacks_handlers
from bot.handlers.nick import setup_nick_handlers
from bot.handlers import (
    start,
    balance,
    transfer,
    history,
    admin,
    dep_kazino
)


def main():
    bot = TeleBot(Config.TOKEN)

    # Регистрация обработчиков
    setup_nick_handlers(bot)
    start.setup_start_handlers(bot)
    balance.setup_balance_handlers(bot)
    transfer.setup_transfer_handlers(bot)
    history.setup_history_handlers(bot)
    admin.setup_admin_handlers(bot)
    setup_help_handlers(bot)
    setup_callbacks_handlers(bot)
    dep_kazino.setup_casino_handlers(bot)
    dep_kazino.setup_4_code(bot)
    admin.transfer_bank(bot)

    print("Bot is running...")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
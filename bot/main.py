from telebot import TeleBot
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
    admin
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

    print("Bot is running...")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
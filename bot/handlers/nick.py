from telebot import types
from bot.database import create_db_connection
from bot.utils.decorators import log_errors
import logging

logger = logging.getLogger(__name__)

def setup_nick_handlers(bot):
    @bot.message_handler(commands=['nick'])
    @log_errors("nick_command")
    def show_all_nicknames(message):
        """Показывает список всех подтвержденных пользователей"""
        connection = None
        cursor = None
        try:
            connection = create_db_connection()
            if not connection:
                bot.reply_to(message, "❌ Ошибка подключения к базе данных")
                return

            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT nickname FROM users WHERE is_verified = TRUE ORDER BY nickname"
            )
            users = cursor.fetchall()

            if users:
                nicknames = [f"👤 {user['nickname']}" for user in users]
                response = "📋 Список пользователей:\n\n" + "\n".join(nicknames)
            else:
                response = "😕 Пока нет зарегистрированных пользователей"

            bot.reply_to(message, response)

        except Exception as e:
            logger.error(f"Nick list error: {str(e)}", exc_info=True)
            bot.reply_to(message, "❌ Ошибка при получении данных")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
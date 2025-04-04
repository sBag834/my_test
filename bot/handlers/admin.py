from telebot import types
from decimal import Decimal
from bot.database import create_db_connection
from bot.utils.decorators import admin_required
from bot.utils.exchange import get_exchange_rate
from bot.utils.notifications import notify_admins
import logging

logger = logging.getLogger(__name__)


def setup_admin_handlers(bot):
    @bot.message_handler(commands=['bl'])
    @admin_required("⛔ Требуются права администратора!")
    def handle_admin_balance(message):
        """Проверка баланса игрока (админская команда)"""
        connection = None
        try:
            args = message.text.split()[1:]
            if not args:
                bot.reply_to(message, "❌ Укажите ник игрока: /bl <ник>")
                return

            nickname = ' '.join(args).strip()
            connection = create_db_connection()

            if not connection:
                bot.reply_to(message, "❌ Ошибка подключения к базе данных")
                return

            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT balance, balance_ar, nickname 
                    FROM users 
                    WHERE nickname = %s
                """, (nickname,))
                user_data = cursor.fetchone()

                if not user_data:
                    bot.reply_to(message, "❌ Пользователь не найден")
                    return

                # Обработка NULL-значений
                balance_es = user_data['balance'] or Decimal('0')
                balance_ar = user_data['balance_ar'] or Decimal('0')

                rate = get_exchange_rate()
                conversion_text = ""
                if rate and rate > 0:
                    converted_ar = balance_es * rate
                    conversion_text = f"\n  ≈ {converted_ar:.2f} Ar (курс {rate:.2f} Ar/Эс)"

                response = (
                    f"👤 Административный запрос:\n"
                    f"Ник: {user_data['nickname']}\n"
                    f"💰 Эссенция: {balance_es:.2f} Эс{conversion_text}\n"
                    f"💰 Ары: {balance_ar:.2f} Ar"
                )
                bot.reply_to(message, response)

        except Exception as e:
            logger.error(f"Admin balance error: {str(e)}", exc_info=True)
            bot.reply_to(message, "⛔ Ошибка выполнения команды")
        finally:
            if connection:
                connection.close()


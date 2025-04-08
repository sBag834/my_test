from telebot import types
from decimal import Decimal
from bot.database import create_db_connection
from bot.utils.exchange import get_exchange_rate
from bot.handlers.crypto_val import get_current_price


def setup_balance_handlers(bot):
    @bot.message_handler(commands=['balance'])
    def show_user_balance(message):
        """Обработчик команды проверки баланса пользователя"""
        connection = None
        cursor = None
        try:
            connection = create_db_connection()
            if not connection:
                bot.reply_to(message, "❌ Ошибка подключения к базе данных")
                return

            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT nickname, balance, balance_ar 
                FROM users 
                WHERE telegram_id = %s
            """, (message.from_user.id,))

            user_data = cursor.fetchone()

            cursor.execute("SELECT balance FROM users WHERE id = 3")
            bought_before = 1000 - cursor.fetchone()['balance'] or 0  # Сколько было куплено до продажи

            if user_data:
                # Получаем балансы с защитой от None
                balance_es = user_data['balance'] or Decimal('0')
                balance_ar = user_data['balance_ar'] or Decimal('0')

                # Конвертация валюты

                total_refund = 0
                remaining_amount = balance_es
                while remaining_amount > 0:
                    current_chunk = min(1, remaining_amount)
                    current_price = Decimal('1') + Decimal('0.1') * (bought_before - 1)  # Цена предыдущей единицы
                    total_refund += current_price * current_chunk
                    bought_before -= current_chunk
                    remaining_amount -= current_chunk

                rate = get_current_price()
                conversion_text = ""
                if rate and rate > 0:
                    conversion_text = f"\n  ≈ {total_refund:.2f} Ar (курс {rate:.2f} Ar/Эс)"

                response = (
                    f"👤 Ник: {user_data['nickname']}\n"
                    f"💰 Эссенция: {balance_es:.2f} Эс{conversion_text}\n"
                    f"💰 Ары: {balance_ar:.2f} Ar\n\n"
                    f"Для операций с валютами посетите банк"
                )
            else:
                response = "⚠ Вы не зарегистрированы. Используйте /start для регистрации"

            bot.reply_to(message, response)

        except Exception as e:
            bot.reply_to(message, "⛔ Ошибка при проверке баланса")
            print(f"Balance error: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
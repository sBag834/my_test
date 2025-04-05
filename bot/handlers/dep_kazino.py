from time import sleep
from telebot import types
from bot.database import create_db_connection
from bot.utils.decorators import log_errors
import logging
from decimal import Decimal, InvalidOperation
import random


logger = logging.getLogger(__name__)

def setup_casino_handlers(bot):
    @bot.message_handler(commands=['dep'])
    @log_errors("transfer_command")
    def handle_transfer(message):
        """
        Обработчик средств в формате:
        /dep <сумма> <множитель>
        """
        try:
            # Парсинг аргументов
            args = message.text.split()[1:]

            # Валидация количества аргументов
            if len(args) != 2:
                bot.reply_to(
                    message,
                    "❌ *Неверный формат!*\n"
                    "Используйте: /dep <сумма> <множитель>\n"
                    "Пример: /dep 10 5",
                    parse_mode="Markdown"
                )
                return

            amount_str, rate_str = args

            try:
                rate = Decimal(rate_str).quantize(Decimal('0.00'))
                if rate < Decimal('2') or rate > Decimal('10'):
                    raise ValueError
            except (ValueError, InvalidOperation):
                bot.reply_to(
                    message,
                    "❌ *Некорректный множитель!*\n"
                    "Множитель может быть от 2 до 10",
                    parse_mode="Markdown"
                )
                return

            # Валидация суммы
            try:
                amount = Decimal(amount_str).quantize(Decimal('0.00'))
                if amount <= Decimal('0'):
                    raise ValueError
            except (ValueError, InvalidOperation):
                bot.reply_to(
                    message,
                    "❌ *Некорректная сумма!*\n"
                    "Примеры правильного ввода:\n"
                    "- `100`\n"
                    "- `50.5`\n"
                    "- `75.00`",
                    parse_mode="Markdown"
                )
                return

            # Выполнение депа
            process_transfer(
                bot=bot,
                sender_id=message.from_user.id,
                rate=rate,
                amount=amount
            )

        except Exception as e:
            logger.error(f"Transfer error: {str(e)}", exc_info=True)
            bot.reply_to(message, "⚠ Произошла критическая ошибка при обработке перевода")



def process_transfer(bot, sender_id: int, rate: Decimal, amount: Decimal):
    connection = None
    cursor = None
    try:
        connection = create_db_connection()
        if not connection:
            bot.send_message(sender_id, "🔧 Ошибка подключения к системе. Попробуйте позже")
            return

        cursor = connection.cursor(dictionary=True)

        # Получаем данные отправителя
        cursor.execute(
            "SELECT id, nickname, balance_ar FROM users WHERE telegram_id = %s",
            (sender_id,)
        )
        sender = cursor.fetchone()

        if not sender:
            bot.send_message(sender_id, "❌ Вы не завершили регистрацию! Используйте /start")
            return

        # Проверка баланса
        balance_field = 'balance_ar'
        sender_balance = sender.get(balance_field, Decimal('0'))
        currency_name = 'Аров'

        if sender_balance < amount:
            bot.send_message(
                sender_id,
                f"❌ Недостаточно {currency_name}!\n"
                f"Ваш баланс: {sender_balance:.2f}"
            )
            return

        # Выполнение транзакции
        try:
            cursor.execute("START TRANSACTION")

            # Списание средств
            cursor.execute(
                f"UPDATE users SET {balance_field} = {balance_field} - %s WHERE id = %s",
                (float(amount), sender['id'])
            )


            # короче тут берётся рейт и происходит ставочка, если она заходит то
            # типу начисляется сумма и пишут что абалдеть, зашла ставка,
            # если нет то пишут анлаки и заканчивается


            bot.send_message(
                sender_id,
                f"Ставочка идёт...\n\n"
            )

            sleep(0.75)
            bot.send_message(
                sender_id,
                f"Ставочка крутится...\n\n"
            )

            sleep(1)
            bot.send_message(
                sender_id,
                f"Ставочка ЗАЛЕТАЕТ??????\n\n"
            )
            sleep(1)

            win_chance = 1 / rate * Decimal('0.9')
            if random.random() < win_chance:
                win_amount = amount * rate

                receiver_field = 'balance_ar'
                cursor.execute(
                    f"UPDATE users SET {receiver_field} = {receiver_field} + %s WHERE id = %s",
                    (float(win_amount), sender['id'])
                )


                new_balance = sender_balance - amount + win_amount
                bot.send_message(
                    sender_id,
                    f"🎉🎉🎉🎉СТАВОЧКА ЗАТЕТЕЛАААА!🎉🎉🎉🎉\n\n"
                    f"Новый баланс: {new_balance:.2f}"
                )
                connection.commit()

                return win_amount
            else:
                new_balance = sender_balance - amount
                bot.send_message(
                    sender_id,
                    f"😭😭😭ставочка не залетела(((😭😭😭\n\n"
                    f"Новый баланс: {new_balance:.2f}"
                )
                connection.commit()
                return 0


        except Exception as e:
            connection.rollback()
            logger.error(f"Transaction failed: {str(e)}")
            bot.send_message(sender_id, "❌ Ошибка при обработке транзакции")
        finally:
            if connection.is_connected():
                cursor.close()

    except Exception as e:
        logger.error(f"Transfer process error: {str(e)}", exc_info=True)
    finally:
        if connection:
            connection.close()
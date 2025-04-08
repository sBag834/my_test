from telebot import types
from decimal import Decimal, InvalidOperation
from bot.database import create_db_connection
from bot.utils.decorators import log_errors
from bot.utils.notifications import notify_transfer
import logging
from html import escape

logger = logging.getLogger(__name__)


def setup_transfer_handlers(bot):
    @bot.message_handler(commands=['tr'])
    @log_errors("transfer_command")
    def handle_transfer(message):
        """
        Обработчик перевода средств в формате:
        /tr <валюта:es/ar> <ник получателя> <сумма>
        """
        try:
            # Парсинг аргументов
            args = message.text.split()[1:]

            # Валидация количества аргументов
            if len(args) != 3:
                bot.reply_to(
                    message,
                    "❌ *Неверный формат!*\n"
                    "Используйте: /tr <валюта> <ник> <сумма>\n"
                    "Пример: /tr es Игрок123 100.50\n"
                    "Валюты: es (Эссенция), ar (Ары)\n"
                    "❗️❗️❗️ Комиссия составляет 5% ❗️❗️❗️",
                    parse_mode="Markdown"
                )
                return

            currency, receiver_nick, amount_str = args
            currency = currency.lower()

            # Проверка валюты
            if currency not in {'es', 'ar'}:
                bot.reply_to(
                    message,
                    "❌ *Недопустимая валюта!*\n"
                    "Доступные варианты:\n"
                    "- `es` для Эссенции\n"
                    "- `ar` для Аров\n"
                    "❗️❗️❗️ Комиссия составляет 5% ❗️❗️❗️",
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
                    "- `75.00`\n"
                    "❗️❗️❗️ Комиссия составляет 5% ❗️❗️❗️",
                    parse_mode="Markdown"
                )
                return

            # Выполнение перевода
            process_transfer(
                bot=bot,
                sender_id=message.from_user.id,
                currency=currency,
                receiver_nick=receiver_nick,
                amount=amount
            )

        except Exception as e:
            logger.error(f"Transfer error: {str(e)}", exc_info=True)
            bot.reply_to(message, "⚠ Произошла критическая ошибка при обработке перевода")


def process_transfer(bot, sender_id: int, currency: str, receiver_nick: str, amount: Decimal):
    """Основная логика выполнения перевода"""
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
            "SELECT id, nickname, balance, balance_ar FROM users WHERE telegram_id = %s",
            (sender_id,)
        )
        sender = cursor.fetchone()

        if not sender:
            bot.send_message(sender_id, "❌ Вы не завершили регистрацию! Используйте /start")
            return

        # Поиск получателя
        cursor.execute(
            "SELECT id, nickname, telegram_id FROM users WHERE nickname = %s AND id != %s",
            (receiver_nick, sender['id'])
        )
        receiver = cursor.fetchone()

        if not receiver:
            bot.send_message(sender_id, f"❌ Пользователь @{receiver_nick} не найден")
            return

        #проверка кто скидывает деньги, если связанно с банком то нит коммисии
        if receiver['telegram_id'] == '0000000000':
            tax = Decimal('0.0')
            amount_tax = amount + tax
        elif currency == 'es':
            tax = Decimal('0.0')
            amount_tax = amount + tax
        else:
            tax = amount * Decimal('0.05')
            amount_tax = amount + tax

        # Проверка баланса
        balance_field = 'balance' if currency == 'es' else 'balance_ar'
        sender_balance = sender.get(balance_field, Decimal('0'))
        currency_name = 'Эссенции' if currency == 'es' else 'Аров'

        if sender_balance < amount_tax and currency == 'ar':
            bot.send_message(
                sender_id,
                f"❌ Недостаточно {currency_name}!\n"
                f"Ваш баланс: {sender_balance:.2f}\n"
                "❗️❗️❗️ Комиссия составляет 5% ❗️❗️❗️"
            )
            return
        elif sender_balance < amount_tax and currency == 'es':
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
                (float(amount_tax), sender['id'])
            )

            # Начисление комиссии банку
            bank_field = 'balance' if currency == 'es' else 'balance_ar'
            cursor.execute(
                f"UPDATE users SET {bank_field} = {bank_field} + %s WHERE id = %s",
                (float(tax), '3')
            )

            # Зачисление средств
            receiver_field = 'balance' if currency == 'es' else 'balance_ar'
            cursor.execute(
                f"UPDATE users SET {receiver_field} = {receiver_field} + %s WHERE id = %s",
                (float(amount), receiver['id'])
            )

            # Запись в историю
            cursor.execute(
                "INSERT INTO transactions (sender_id, receiver_id, amount, currency) VALUES (%s, %s, %s, %s)",
                (sender['id'], receiver['id'], float(amount), currency)
            )

            connection.commit()

            # Экранирование спецсимволов в никнеймах
            safe_sender_nick = escape(sender['nickname'])
            safe_receiver_nick = escape(receiver['nickname'])

            # Уведомление отправителю
            new_balance = sender_balance - amount_tax
            bot.send_message(
                sender_id,
                f"✅ Перевод выполнен!\n\n"
                f"Сумма: {amount:.2f} {currency_name}\n"
                f"Комиссия составила: {tax:.2f}\n"
                f"Получатель: {safe_receiver_nick}\n"
                f"Новый баланс: {new_balance:.2f}"
            )

            # Уведомление получателю
            if receiver.get('telegram_id'):
                try:
                    bot.send_message(
                        receiver['telegram_id'],
                        f"💸 Вам перевели {amount:.2f} {currency_name} от {safe_sender_nick}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка уведомления: {str(e)}")

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
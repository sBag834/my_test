from telebot import types
from decimal import Decimal, InvalidOperation
from bot.database import create_db_connection
from bot.utils.decorators import admin_required
from bot.utils.exchange import get_exchange_rate
from bot.utils.notifications import notify_admins
import logging
from html import escape

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



def transfer_bank(bot):
    @bot.message_handler(commands=['pay'])
    @admin_required("⛔ Требуются права администратора!")
    def handle_transfer_bank(message):
        """
        Обработчик перевода средств в формате:
        /pay <валюта:es/ar> <ник получателя> <сумма>
        """
        try:
            # Парсинг аргументов
            args = message.text.split()[1:]

            # Валидация количества аргументов
            if len(args) != 3:
                bot.reply_to(
                    message,
                    "❌ *Неверный формат!*\n"
                    "Используйте: /pay <валюта> <ник> <сумма>\n"
                    "Пример: /pay es Игрок123 100.50\n"
                    "Валюты: es (Эссенция), ar (Ары)",
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
                    "- `ar` для Аров",
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

            # Выполнение перевода
            process_transfer_bank(
                bot=bot,
                sender_id=0000000000,
                id_adm=827491832,
                currency=currency,
                receiver_nick=receiver_nick,
                amount=amount
            )

        except Exception as e:
            logger.error(f"Transfer error: {str(e)}", exc_info=True)
            bot.reply_to(message, "⚠ Произошла критическая ошибка при обработке перевода")


def process_transfer_bank(bot, sender_id: int, id_adm: int, currency: str, receiver_nick: str, amount: Decimal):
    """Основная логика выполнения перевода"""
    connection = None
    cursor = None
    try:
        connection = create_db_connection()
        if not connection:
            bot.send_message(id_adm, "🔧 Ошибка подключения к системе. Попробуйте позже")
            return

        cursor = connection.cursor(dictionary=True)

        # Получаем данные отправителя
        cursor.execute(
            "SELECT id, nickname, balance, balance_ar FROM users WHERE telegram_id = %s",
            (sender_id,)
        )
        sender = cursor.fetchone()


        # Поиск получателя
        cursor.execute(
            "SELECT id, nickname, telegram_id FROM users WHERE nickname = %s AND id != %s",
            (receiver_nick, sender['id'])
        )
        receiver = cursor.fetchone()

        if not receiver:
            bot.send_message(id_adm, f"❌ Пользователь {receiver_nick} не найден")
            return

        # Проверка баланса
        balance_field = 'balance' if currency == 'es' else 'balance_ar'
        sender_balance = sender.get(balance_field, Decimal('0'))
        currency_name = 'Эссенции' if currency == 'es' else 'Аров'

        if sender_balance < amount:
            bot.send_message(
                id_adm,
                f"❌ Недостаточно {currency_name}!\n"
                f"Баланс банка: {sender_balance:.2f}"
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
            new_balance = sender_balance - amount
            bot.send_message(
                id_adm,
                f"✅ Перевод выполнен!\n\n"
                f"Сумма: {amount:.2f} {currency_name}\n"
                f"Получатель: {safe_receiver_nick}\n"
                f"Новый баланс банка: {new_balance:.2f}"
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
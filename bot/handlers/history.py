from decimal import Decimal
from telebot import types
from bot.database import create_db_connection

def setup_history_handlers(bot):
    @bot.message_handler(commands=['history'])
    def show_history(message):
        """Обработчик команды просмотра истории операций"""
        connection = None
        try:
            # Парсинг номера страницы
            try:
                page = int(message.text.split()[1]) if len(message.text.split()) > 1 else 1
                page = max(1, page)
            except ValueError:
                page = 1

            connection = create_db_connection()
            if not connection:
                bot.reply_to(message, "❌ Ошибка подключения к базе")
                return

            with connection.cursor(dictionary=True) as cursor:
                # Получение ID пользователя
                cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (message.from_user.id,))
                user = cursor.fetchone()

                if not user:
                    bot.reply_to(message, "❌ Вы не зарегистрированы")
                    return

                # Подсчет общего количества операций
                cursor.execute("""
                    SELECT COUNT(*) as total 
                    FROM transactions 
                    WHERE sender_id = %s OR receiver_id = %s
                """, (user['id'], user['id']))
                total = cursor.fetchone()['total']
                pages = max(1, (total + 9) // 10)

                # Получение транзакций для текущей страницы
                cursor.execute("""
                    SELECT 
                        t.amount,
                        t.timestamp,
                        sender.nickname as sender_nick,
                        receiver.nickname as receiver_nick,
                        t.sender_id,
                        t.receiver_id,
                        t.currency
                    FROM transactions t
                    JOIN users sender ON t.sender_id = sender.id
                    JOIN users receiver ON t.receiver_id = receiver.id
                    WHERE t.sender_id = %s OR t.receiver_id = %s
                    ORDER BY t.timestamp DESC
                    LIMIT 10 OFFSET %s
                """, (user['id'], user['id'], (page - 1) * 10))

                transactions = cursor.fetchall()

                if transactions:
                    history = []
                    for t in transactions:
                        amount = Decimal(t['amount']).quantize(Decimal('0.00'))
                        timestamp = t['timestamp'].strftime('%d.%m %H:%M')
                        currency = t['currency'].upper()

                        if t['sender_id'] == user['id']:
                            entry = (
                                f"🔴 Отправлено: {amount} {currency}\n"
                                f"→ Для: {t['receiver_nick']}\n"
                                f"⏰ {timestamp}"
                            )
                        else:
                            entry = (
                                f"🟢 Получено: {amount} {currency}\n"
                                f"← От: {t['sender_nick']}\n"
                                f"⏰ {timestamp}"
                            )
                        history.append(entry)

                    response = (
                        f"📜 История операций (стр. {page}/{pages}):\n\n" +
                        "\n\n".join(history) +
                        f"\n\nИспользуйте /history <номер> для навигации"
                    )
                else:
                    response = "📭 У вас пока нет операций"

                bot.send_message(message.chat.id, response)

        except Exception as e:
            bot.reply_to(message, "❌ Ошибка при загрузке истории")
            print(f"History error: {e}")
        finally:
            if connection:
                connection.close()
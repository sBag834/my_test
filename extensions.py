import telebot
from telebot import types
import mysql.connector
from mysql.connector import Error
from decimal import Decimal, InvalidOperation, getcontext
import os
from dotenv import load_dotenv

load_dotenv()

#конфигурация
TOKEN = os.getenv('BOT_TOKEN')
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}
getcontext().prec = 10

#инициализировать бота
bot = telebot.TeleBot(TOKEN)


#подключени к базе данных
def create_db_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")
    return connection

#чтение текущего курса из файла с обработкой ошибок
def get_exchange_rate():
    try:
        with open('current_number.txt', 'r', encoding='utf-8') as f:
            rate_str = f.read().strip().replace(',', '.')
            return Decimal(rate_str)
    except FileNotFoundError:
        print("Файл курса не найден")
        return None
    except (ValueError, InvalidOperation) as e:
        print(f"Ошибка формата курса: {e}")
        return None
    except Exception as e:
        print(f"Ошибка чтения курса: {e}")
        return None

#проверка на админа
def is_admin(user_id):
    connection = create_db_connection()
    if not connection:
        return False

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT is_admin FROM users WHERE telegram_id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            return user and user['is_admin']
    except Error as e:
        print(f"Admin check error: {e}")
        return False
    finally:
        connection.close()

#обработчики команд
@bot.message_handler(commands=['start'])
def send_welcome(message):
    connection = create_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (message.from_user.id,))
        user = cursor.fetchone()

        if user:
            if user['is_verified']:
                bot.reply_to(message, f"Здарова, {user['nickname']}!\n"
                             "что бы узнать список команд отправь /help\n"
                             "\n"
                             "мяу")
            else:
                bot.reply_to(message, "Ваша регистрация все еще находится на стадии утверждения.")
        else:
            msg = bot.reply_to(message, "Добро пожаловать! Чтобы зарегистрироваться, пожалуйста, пришлите мне свой ник из майнкрафта:")
            bot.register_next_step_handler(msg, process_nickname_step)

        cursor.close()
        connection.close()


@bot.message_handler(commands=['help'])
def help_1(message):
    bot.reply_to(message, "Команда чтобы посмотреть список всех ников пользователей которым можно совершить перевод: /nick\n"
                          "Команда чтобы посмотреть баланс: /balance\n"
                          "перевод /transfer\n"
                          "история /history")


@bot.message_handler(commands=['nick'])
def show_all_nicknames(message):
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)

            #получаем все подтвержденные никнеймы из базы
            cursor.execute("SELECT nickname FROM users WHERE is_verified = TRUE ORDER BY nickname")
            users = cursor.fetchall()

            if users:
                #формируем список
                nicknames = [user['nickname'] for user in users]
                response = "📋 Список всех пользователей:\n\n" + "\n".join(f"👤 {nickname}" for nickname in nicknames)
            else:
                response = "😕 пока нет пользователей."

            bot.reply_to(message, response)

        except Error as e:
            bot.reply_to(message, "Произошла ошибка при получении данных")
            print(f"Database error: {e}")
        finally:
            cursor.close()
            connection.close()
    else:
        bot.reply_to(message, "Ошибка подключения к базе данных")


@bot.message_handler(commands=['balance'])
def show_user_balance(message):
    try:
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)

            cursor.execute("""
                SELECT nickname, balance, balance_ar 
                FROM users 
                WHERE telegram_id = %s
            """, (message.from_user.id,))

            user_data = cursor.fetchone()

            if user_data:
                balance_es = user_data['balance'] if user_data['balance'] is not None else Decimal('0')
                balance_ar = user_data['balance_ar'] if user_data['balance_ar'] is not None else Decimal('0')

                rate = get_exchange_rate()
                conversion_text = ""
                if rate is not None and rate > 0:
                    converted_ar = balance_es * rate
                    conversion_text = f"\n  ≈ {converted_ar:.2f} Ar (по курсу {rate:.2f} Ar/Эс)"

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
        bot.reply_to(message, "⛔ Произошла ошибка при проверке баланса")
        print(f"Error in /balance: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()


@bot.message_handler(commands=['transfer'])
def start_transfer(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Эс (ES)', 'Ар (AR)')
    msg = bot.reply_to(message, "💰 Выберите валюту для перевода:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_currency_choice)


def process_currency_choice(message):
    currency = message.text.lower()
    if currency not in ['эс (es)', 'ар (ar)']:
        bot.reply_to(message, "❌ Неверный выбор валюты")
        return

    currency_type = 'es' if 'эс' in currency else 'ar'
    user_data = {'currency': currency_type}

    msg = bot.reply_to(message,
                       f"💸 Введите никнейм получателя и сумму в формате:\n<никнейм> <сумма>\nПример: user 50.50",
                       reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_transfer_step, currency_type)


@bot.message_handler(commands=['history'])
def show_history(message):
    try:
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
            cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (message.from_user.id,))
            user = cursor.fetchone()

            if not user:
                bot.reply_to(message, "❌ Вы не зарегистрированы")
                return

            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM transactions 
                WHERE sender_id = %s OR receiver_id = %s
            """, (user['id'], user['id']))
            total = cursor.fetchone()['total']
            pages = max(1, (total + 9) // 10)

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


def process_transfer_step(message, currency_type):
    connection = None
    cursor = None
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ Неверный формат. Используйте: <никнейм> <сумма>")
            return

        receiver_nickname, amount_str = parts
        try:
            amount = Decimal(amount_str).quantize(Decimal('0.00'))
            if amount <= Decimal('0'):
                bot.reply_to(message, "❌ Сумма должна быть больше 0")
                return
        except Exception:
            bot.reply_to(message, "❌ Неверная сумма. Введите число (например: 100 или 50.50)")
            return

        connection = create_db_connection()
        if not connection:
            bot.reply_to(message, "❌ Ошибка подключения к базе")
            return

        cursor = connection.cursor(dictionary=True)

        # Проверяем отправителя
        cursor.execute(
            "SELECT id, nickname, balance, balance_ar FROM users WHERE telegram_id = %s",
            (message.from_user.id,)
        )
        sender = cursor.fetchone()

        if not sender:
            bot.reply_to(message, "❌ Вы не зарегистрированы")
            return

        # Проверяем баланс в зависимости от валюты
        balance_field = 'balance' if currency_type == 'es' else 'balance_ar'
        sender_balance = Decimal(str(sender[balance_field]))

        if sender_balance < amount:
            currency_name = 'Эс' if currency_type == 'es' else 'Ар'
            bot.reply_to(message,
                         f"❌ Недостаточно {currency_name}. Ваш баланс: {sender_balance:.2f} {currency_name.upper()}")
            return

        # Проверяем получателя
        cursor.execute("""
            SELECT id, nickname, telegram_id 
            FROM users 
            WHERE nickname = %s AND id != %s
        """, (receiver_nickname, sender['id']))
        receiver = cursor.fetchone()

        if not receiver:
            bot.reply_to(message, "❌ Получатель не найден или это вы сами")
            return

        # Выполняем перевод
        try:
            # Сбрасываем возможные предыдущие транзакции
            connection.rollback()

            # Явно начинаем новую транзакцию
            cursor.execute("START TRANSACTION")

            # Обновление баланса отправителя
            cursor.execute(f"""
                    UPDATE users 
                    SET {balance_field} = {balance_field} - %s 
                    WHERE id = %s
                """, (float(amount), sender['id']))

            # Обновление баланса получателя
            receiver_field = 'balance' if currency_type == 'es' else 'balance_ar'
            cursor.execute(f"""
                    UPDATE users 
                    SET {receiver_field} = {receiver_field} + %s 
                    WHERE id = %s
                """, (float(amount), receiver['id']))

            # Запись в историю
            cursor.execute("""
                    INSERT INTO transactions 
                    (sender_id, receiver_id, amount, currency)
                    VALUES (%s, %s, %s, %s)
                """, (sender['id'], receiver['id'], float(amount), currency_type))

            connection.commit()

            # Формирование сообщения
            currency_symbol = 'Эс' if currency_type == 'es' else 'Ar'
            new_balance = sender_balance - amount
            response = (
                f"✅ Перевод {amount:.2f} {currency_symbol} выполнен!\n"
                f"• Получатель: {receiver['nickname']}\n"
                f"• Новый баланс: {new_balance:.2f} {currency_symbol}"
            )

            bot.reply_to(message, response)

            # Уведомление получателя
            if receiver.get('telegram_id'):
                try:
                    bot.send_message(
                        chat_id=receiver['telegram_id'],
                        text=(
                            f"💸 Вам поступил перевод!\n"
                            f"• От: {sender['nickname']}\n"
                            f"• Сумма: {amount:.2f} {currency_symbol}\n"
                            f"• Используйте /balance для проверки"
                        )
                    )
                except Exception as e:
                    print(f"Ошибка уведомления: {e}")

        except Exception as e:
            connection.rollback()
            bot.reply_to(message, "❌ Ошибка при переводе средств")
            print(f"Ошибка транзакции: {e}")

    except Exception as e:
        bot.reply_to(message, "❌ Произошла ошибка")
        print(f"Ошибка в процессе перевода: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def process_nickname_step(message):
    try:
        nickname = message.text

        #проверьте, действителен ли ник
        if len(nickname) < 3 or len(nickname) > 25:
            bot.reply_to(message, "Длина псевдонима должна составлять от 3 до 25 символов. Пожалуйста, попробуйте снова.")
            return

        connection = create_db_connection()
        if connection:
            cursor = connection.cursor()

            # проверьте, занят ли уже псевдоним
            cursor.execute("SELECT * FROM users WHERE nickname = %s", (nickname,))
            if cursor.fetchone():
                bot.reply_to(message, "Этот ник уже занят. Пожалуйста, выберите другой.")
                return

            cursor.execute(
                "INSERT INTO users (telegram_id, nickname) VALUES (%s, %s)",
                (message.from_user.id, nickname)
            )
            connection.commit()

            notify_admin(message.from_user.id, nickname)

            bot.reply_to(message, "Благодарим вас за регистрацию! Ваша учетная запись ожидает одобрения администратора.")

            cursor.close()
            connection.close()
    except Exception as e:
        bot.reply_to(message, "Что-то пошло не так. Пожалуйста, повторите попытку позже.")
        print(f"Error: {e}")


def notify_admin(user_id, nickname):
    connection = create_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT telegram_id FROM users WHERE is_admin = TRUE")
        admins = cursor.fetchall()

        for admin in admins:
            markup = types.InlineKeyboardMarkup()
            approve_btn = types.InlineKeyboardButton(
                "Approve",
                callback_data=f"approve_{user_id}"
            )
            reject_btn = types.InlineKeyboardButton(
                "Reject",
                callback_data=f"reject_{user_id}"
            )
            markup.add(approve_btn, reject_btn)

            bot.send_message(
                admin['telegram_id'],
                f"Запрос на новую регистрацию:\n\nUser ID: {user_id}\nNickname: {nickname}\n\nОдобрить этого пользователя?",
                reply_markup=markup
            )

        cursor.close()
        connection.close()


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data.startswith("approve_") or call.data.startswith("reject_"):
        user_id = int(call.data.split("_")[1])

        connection = create_db_connection()
        if connection:
            cursor = connection.cursor()

            if call.data.startswith("approve_"):
                cursor.execute(
                    "UPDATE users SET is_verified = TRUE WHERE telegram_id = %s",
                    (user_id,)
                )
                connection.commit()

                bot.send_message(
                    user_id,
                    "Ваша регистрация одобрена! Теперь вы можете использовать бота."
                )

                bot.answer_callback_query(
                    call.id,
                    "Пользователь успешно одобрен!",
                    show_alert=False
                )
                bot.edit_message_text(
                    "Регистрация одобрена.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
            else:
                cursor.execute(
                    "DELETE FROM users WHERE telegram_id = %s",
                    (user_id,)
                )
                connection.commit()

                bot.send_message(
                    user_id,
                    "Ваша регистрация была отклонена администратором."
                )

                bot.answer_callback_query(
                    call.id,
                    "Пользователь отклонен!",
                    show_alert=False
                )
                bot.edit_message_text(
                    "Регистрация отклонена.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )

            cursor.close()
            connection.close()



#для админа
@bot.message_handler(commands=['bl'])
def handle_admin_balance(message):
    try:
        # Проверка прав администратора
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ Команда доступна только администраторам")
            return

        # Парсим аргументы команды
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
            # Ищем пользователя по нику
            cursor.execute("""
                SELECT balance, balance_ar, nickname 
                FROM users 
                WHERE nickname = %s
            """, (nickname,))
            user_data = cursor.fetchone()

            if not user_data:
                bot.reply_to(message, "❌ Пользователь не найден")
                return

            # Рассчитываем конвертацию
            rate = get_exchange_rate()
            conversion_text = ""
            if rate and rate > 0:
                converted_ar = user_data['balance'] * rate
                conversion_text = f"\n  ≈ {converted_ar:.2f} Ar (курс {rate:.2f} Ar/Эс)"

            # Формируем ответ
            response = (
                f"👤 Административный запрос:\n"
                f"Ник: {user_data['nickname']}\n"
                f"💰 Эссенция: {user_data['balance']:.2f} Эс{conversion_text}\n"
                f"💰 Ары: {user_data['balance_ar']:.2f} Ar"
            )
            bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, "⛔ Ошибка выполнения команды")
        print(f"Admin balance error: {e}")
    finally:
        if connection:
            connection.close()



print("Bot is running...")
bot.infinity_polling()
from telebot import types
from bot.database import create_db_connection
from bot.utils.notifications import notify_admins


def setup_start_handlers(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        """Обработчик команды старта и регистрации"""
        connection = create_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT * FROM users WHERE telegram_id = %s",
                    (message.from_user.id,)
                )
                user = cursor.fetchone()

                if user:
                    if user['is_verified']:
                        response = (
                            f"Здарова, {user['nickname']}!\n"
                            "Что бы узнать список команд отправь /help\n\n"
                            "мяу"
                        )
                    else:
                        response = "Ваша регистрация все еще находится на стадии утверждения."
                    bot.reply_to(message, response)
                else:
                    msg = bot.reply_to(
                        message,
                        "Добро пожаловать! Для регистрации пришлите ваш игровой ник:",
                        reply_markup=types.ForceReply(selective=False)
                    )
                    bot.register_next_step_handler(msg, process_nickname_step)

            except Exception as e:
                bot.reply_to(message, "⚠ Ошибка при обработке запроса")
                print(f"Start error: {e}")
            finally:
                cursor.close()
                connection.close()
        else:
            bot.reply_to(message, "❌ Ошибка подключения к базе данных")

    def process_nickname_step(message):
        """Обработка ввода никнейма"""
        try:
            nickname = message.text.strip()

            if len(nickname) < 3 or len(nickname) > 25:
                return bot.reply_to(
                    message,
                    "❌ Ник должен быть от 3 до 25 символов. Попробуйте снова:"
                )

            connection = create_db_connection()
            if not connection:
                return bot.reply_to(message, "❌ Ошибка подключения к базе")

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM users WHERE nickname = %s",
                    (nickname,)
                )
                if cursor.fetchone():
                    bot.reply_to(message, "❌ Этот ник уже занят. Выберите другой:")
                    bot.register_next_step_handler(message, process_nickname_step)
                    return

                cursor.execute(
                    "INSERT INTO users (telegram_id, nickname) VALUES (%s, %s)",
                    (message.from_user.id, nickname)
                )
                connection.commit()

                notify_admins(bot, message.from_user.id, nickname)
                bot.reply_to(
                    message,
                    "✅ Заявка на регистрацию отправлена! Ожидайте подтверждения."
                )

        except Exception as e:
            bot.reply_to(message, "⚠ Ошибка при регистрации")
            print(f"Registration error: {e}")
        finally:
            if connection:
                connection.close()
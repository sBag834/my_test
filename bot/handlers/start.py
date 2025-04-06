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

                    bot.send_message(
                        message.from_user.id,
                        f"1. Общие положения\n\n"
                        f"1.1. Настоящая оферта определяет условия предоставления банковских услуг в игре Minecraft на сервере 'Essence' (далее — Сервер).\n"
                        f"1.2. Банк 'Essence Bank' (далее — Банк) предоставляет игрокам возможность хранения, обмена и выдачи игровой валюты (полного распоряжения своими средствами) на сервере.\n"
                        f"1.3. Администрация Сервера вправе изменять условия оферты, уведомляя игроков через Discord. Условия изменения будут вступать в силу спустя два дня после оглашения.\n"
                    )

                    bot.send_message(
                        message.from_user.id,
                        f"2. Условия обслуживания\n\n"
                        f"2.1. Открытие счёта:\n"
                        f"• Игрок может открыть счёт в Банке, внеся минимальный депозит в размере 5 ар.\n"
                        f"• Каждый игрок может иметь только один счёт.\n"
                    )

                    bot.send_message(
                        message.from_user.id,
                        f"3. Операции по счету\n\n"
                        f"3.1. Пополнение:\n"
                        f"• Внесение средств происходит непосредственно в филиале Банка.\n"
                        f"3.2. Снятие:\n"
                        f"• Снятие так же происходит только непосредственно в филиале Банка.\n"
                        f"3.3. Переводы:\n"
                        f"• Возможность перевода средств другим игрокам.\n"
                        f"• При переводе игрокам будет взыматься комиссия в размере 5% за счёт отправителя.\n"
                    )

                    bot.send_message(
                        message.from_user.id,
                        f"4. Ответственность и риски\n\n"
                        f"4.1. Банк не несёт ответственности за:\n"
                        f"• Потерю средств из-за багов/взломов сервера (если это не вина банка или администрации).\n"
                        f"4.2. Заморозка счёта.\n"
                        f"• При нарушении правил сервера (читы, дюпы и т.д.) счёт может быть заморожен.\n"
                        f"\n"
                        f"❗️Отправляя ник, вы автоматически принимаете офёрту❗️\n"
                    )

                    msg = bot.reply_to(
                        message,
                        "Если вы согласны с офертой, то пришлите ваш игровой ник:",
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
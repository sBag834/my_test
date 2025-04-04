from telebot import types
from bot.database import create_db_connection
from typing import Optional, List


def notify_admins(bot, user_id: int, nickname: str) -> None:
    """Уведомление администраторов о новой регистрации без разметки"""
    connection = create_db_connection()
    if not connection:
        return

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT telegram_id FROM users WHERE is_admin = TRUE")
            admins = cursor.fetchall()

            for admin in admins:
                try:
                    markup = types.InlineKeyboardMarkup()
                    markup.row(
                        types.InlineKeyboardButton(
                            "✅ Одобрить",
                            callback_data=f"approve_{user_id}"
                        ),
                        types.InlineKeyboardButton(
                            "❌ Отклонить",
                            callback_data=f"reject_{user_id}"
                        )
                    )

                    # Убираем все спецсимволы и форматирование
                    clean_text = (
                        f"Новая регистрация:\n"
                        f"ID: {user_id}\n"
                        f"Ник: {nickname}"
                    )

                    bot.send_message(
                        chat_id=admin['telegram_id'],
                        text=clean_text,
                        reply_markup=markup,
                        parse_mode=None  # Отключаем парсинг
                    )
                except Exception as e:
                    print(f"Ошибка уведомления админа {admin['telegram_id']}: {str(e)}")
    except Exception as e:
        print(f"Ошибка при получении админов: {str(e)}")
    finally:
        connection.close()


def notify_transfer(
    bot,
    recipient_id: int,
    sender_nick: str,
    amount: float,
    currency: str,
    keyboard: Optional[types.ReplyKeyboardMarkup] = None
) -> None:
    """
    Отправляет уведомление о получении перевода.
    """
    try:
        message = (
            f"💸 Новый перевод!\n"
            f"• От: {sender_nick}\n"
            f"• Сумма: {amount:.2f} {currency}\n"
            f"• Проверить: /balance"
        )
        bot.send_message(
            chat_id=recipient_id,
            text=message,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Ошибка уведомления пользователя {recipient_id}: {str(e)}")


def broadcast_to_users(
    bot,
    user_ids: List[int],
    message: str,
    parse_mode: Optional[str] = None
) -> None:
    """
    Массовая рассылка сообщений пользователям с обработкой ошибок.
    """
    for user_id in user_ids:
        try:
            bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode
            )
        except Exception as e:
            print(f"Ошибка рассылки пользователю {user_id}: {str(e)}")
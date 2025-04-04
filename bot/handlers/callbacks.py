from telebot import types
from bot.database import create_db_connection
import logging

logger = logging.getLogger(__name__)


def setup_callbacks_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
    def handle_registration_decision(call):
        """Обработка решений по заявкам"""
        connection = None
        try:
            action, user_id = call.data.split("_")
            user_id = int(user_id)

            connection = create_db_connection()
            if not connection:
                bot.answer_callback_query(call.id, "❌ Ошибка подключения к БД")
                return

            with connection.cursor() as cursor:
                if action == "approve":
                    cursor.execute(
                        "UPDATE users SET is_verified = TRUE WHERE telegram_id = %s",
                        (user_id,)
                    )
                    message_text = "✅ Заявка одобрена"

                    # Уведомляем пользователя
                    try:
                        bot.send_message(user_id, "🎉 Ваша регистрация одобрена!")
                    except Exception as e:
                        logger.error(f"Ошибка уведомления пользователя: {str(e)}")

                else:
                    cursor.execute(
                        "DELETE FROM users WHERE telegram_id = %s",
                        (user_id,)
                    )
                    message_text = "❌ Заявка отклонена"

                connection.commit()

                # Обновляем сообщение у админа
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"{call.message.text}\n\n{message_text}",
                    reply_markup=None
                )

                bot.answer_callback_query(call.id, message_text)

        except Exception as e:
            bot.answer_callback_query(call.id, "⚠ Ошибка обработки запроса")
            logger.error(f"Callback error: {str(e)}", exc_info=True)
        finally:
            if connection:
                connection.close()
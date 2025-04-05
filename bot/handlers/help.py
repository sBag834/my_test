from bot.utils.decorators import log_errors, is_admin_cached


def setup_help_handlers(bot):
    @bot.message_handler(commands=['help'])
    @log_errors("help_command")
    def show_help(message):
        """Обработчик команды помощи"""
        help_text = generate_help_text(message.from_user.id)
        bot.reply_to(message, help_text, parse_mode="Markdown")

    def generate_help_text(user_id: int) -> str:
        """Генерирует текст помощи в зависимости от прав пользователя"""
        base_help = (
            "📚 *Доступные команды:*\n\n"
            "• /start - Начать работу с ботом\n"
            "• /balance - Проверить баланс\n"
            "• /tr <валюта> <ник> <сумма> - Перевод средств\n"
            "   Пример: /tr es Игрок123 100.50\n"
            "   Валюта: es (Эссенция), ar (Ары)\n"
            "• /history - История операций\n"
            "• /nick - Список пользователей\n"
        )

        admin_help = (
            "\n🔐 *Административные команды:*\n\n"
            "• /bl <ник> - Проверить баланс игрока\n"
            "• /pop - чекнуть команду для казика"
        ) if is_admin_cached(user_id) else ""

        return base_help + admin_help
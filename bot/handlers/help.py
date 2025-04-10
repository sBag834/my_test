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
            "• /buy <сумма> - Купить Ессенцию\n"
            "• /sell <сумма> - Продать Ессенцию\n"
            "• /price - Узнать курс Ессенции\n"
            "\n"
            "❗️ Комиссия на переводы между игроками составляет 5% ❗️\n"
        )

        admin_help = (
            "\n🔐 *Административные команды:*\n\n"
            "• /bl <ник> - Проверить баланс игрока\n"
            "• /pop - чекнуть команду для казика\n"
            "• /pay <валюта> <ник> <сумма> - Перевод средств из банка\n"
            "   Пример: /pay es Игрок123 100.50\n"
            "   Валюта: es (Эссенция), ar (Ары)\n"
            "• /in_cash - пополнить счёт банка при помощи налички\n"
            "• /out_cash - снять наличку со счёта банка\n"
        ) if is_admin_cached(user_id) else ""

        return base_help + admin_help
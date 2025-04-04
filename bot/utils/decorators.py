from functools import wraps
from cachetools import TTLCache, cached
from typing import Callable, Optional
from telebot import types
from bot.database import create_db_connection
import logging

# Инициализация кэша для проверки прав администратора
admin_cache = TTLCache(maxsize=128, ttl=300)  # 5 минут кэширования
logger = logging.getLogger(__name__)


def admin_required(response_text: str = "⛔ Команда доступна только администраторам"):
    """
    Декоратор для проверки прав администратора.
    Автоматически отправляет сообщение об ошибке при отсутствии прав.

    Аргументы:
        response_text (str): Текст сообщения при отсутствии прав
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(message: types.Message, *args, **kwargs):
            if not is_admin_cached(message.from_user.id):
                bot = args[0] if args else kwargs.get('bot')
                if bot:
                    bot.reply_to(message, response_text)
                return
            return func(message, *args, **kwargs)

        return wrapper

    return decorator


@cached(admin_cache)
def is_admin_cached(user_id: int) -> bool:
    """Кэшированная проверка прав администратора"""
    connection = create_db_connection()
    if not connection:
        return False

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT is_admin FROM users WHERE telegram_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            return bool(result and result['is_admin'])
    except Exception as e:
        logger.error(f"Admin check error: {str(e)}")
        return False
    finally:
        connection.close()


def database_connection(retries: int = 3):
    """
    Декоратор для автоматического управления подключениями к БД.
    Обрабатывает повторные попытки подключения.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            connection = None
            for attempt in range(1, retries + 1):
                try:
                    connection = create_db_connection()
                    if connection:
                        kwargs['connection'] = connection
                        return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"DB connection attempt {attempt} failed: {str(e)}")
                    if attempt == retries:
                        raise
            return None

        return wrapper

    return decorator


def log_errors(command_name: Optional[str] = None):
    """
    Декоратор для логирования ошибок в обработчиках команд.
    Записывает ошибки в лог с указанием команды.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(message: types.Message, *args, **kwargs):
            try:
                return func(message, *args, **kwargs)
            except Exception as e:
                cmd = command_name or func.__name__
                error_msg = f"Error in {cmd}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                bot = args[0] if args else kwargs.get('bot')
                if bot:
                    bot.reply_to(message, "⚠ Произошла ошибка при выполнении команды")

        return wrapper

    return decorator
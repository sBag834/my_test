from decimal import Decimal, InvalidOperation
import logging
import os

# Настройка логгера
logger = logging.getLogger(__name__)


def get_exchange_rate(file_path: str = 'current_number.txt') -> Decimal | None:
    """
    Получает текущий курс обмена из файла.

    Аргументы:
        file_path (str): Путь к файлу с курсом. По умолчанию 'current_number.txt'

    Возвращает:
        Decimal: Актуальный курс обмена
        None: В случае ошибки чтения или парсинга
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

            # Проверка пустого файла
            if not content:
                logger.error("Файл курса пуст")
                return None

            # Замена разделителей и очистка данных
            rate_str = content.replace(',', '.').replace(' ', '')

            return Decimal(rate_str)

    except FileNotFoundError:
        logger.error(f"Файл курса не найден: {os.path.abspath(file_path)}")
        return None
    except (ValueError, InvalidOperation) as e:
        logger.error(f"Ошибка формата курса: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {str(e)}")
        return None
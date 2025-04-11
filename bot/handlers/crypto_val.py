from telebot import types
from unicodedata import decimal

from bot.database import create_db_connection
from decimal import Decimal
from bot.utils.decorators import admin_required

def get_current_price():
    connection = None
    cursor = None

    connection = create_db_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
                      SELECT balance 
                      FROM users 
                      WHERE id = 3
                  """)

    user_data = cursor.fetchone()
    balance_es = user_data['balance'] or Decimal('0')
    bought = 1000 - balance_es
    cursor.close()
    connection.close()
    return Decimal('1') + Decimal('0.08') * bought


def buy_crypto(user_id, amount):
    """Покупка дробного количества криптовалюты."""
    if amount <= 0:
        return "Количество должно быть больше нуля!"

    connection = None
    cursor = None

    connection = create_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Проверяем, сколько крипты осталось в банке
    cursor.execute("SELECT balance FROM users WHERE id = 3")
    bank_crypto = cursor.fetchone()['balance']

    if bank_crypto < amount:
        return f"В банке недостаточно Эссенции! Доступно для покупки: {bank_crypto:.2f}"

    # Рассчитываем общую стоимость
    cursor.execute("SELECT balance FROM users WHERE id = 3")
    bought_before = 1000 - cursor.fetchone()['balance'] or 0  # Сколько уже куплено


    total_cost = 0
    remaining_amount = amount

    # Цена растёт на 0.1 за каждую полную единицу
    while remaining_amount > 0:
        current_chunk = min(1, remaining_amount)  # Берём 1 или остаток
        current_price = Decimal('1') + Decimal('0.08') * bought_before
        total_cost += current_price * current_chunk
        bought_before += current_chunk
        remaining_amount -= current_chunk

    # Проверяем баланс игрока
    cursor.execute("SELECT balance_ar FROM users WHERE telegram_id = %s", (user_id,))
    user_money = cursor.fetchone()['balance_ar']

    if user_money < total_cost:
        return f"Недостаточно Ар! Нужно: {total_cost:.2f}"

    # Обновляем балансы
    cursor.execute(
        "UPDATE users SET balance_ar = balance_ar - %s, balance = balance + %s WHERE telegram_id = %s",
        (total_cost, amount, user_id))
    cursor.execute(
        "UPDATE users SET balance = balance - %s, balance_ar = balance_ar + %s WHERE id = 3",
        (amount, total_cost))
    connection.commit()
    cursor.close()
    connection.close()

    return f"Куплено {amount:.2f} Эссенции за {total_cost:.2f} Ар (средняя цена: {total_cost / amount:.2f})"


def sell_crypto(user_id, amount):
    """Продажа дробного количества криптовалюты."""
    if amount <= 0:
        return "Количество должно быть больше нуля!"

    connection = None
    cursor = None

    connection = create_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Проверяем баланс игрока
    cursor.execute("SELECT balance FROM users WHERE telegram_id = %s", (user_id,))
    user_crypto = cursor.fetchone()['balance']

    if user_crypto < amount:
        return f"У вас недостаточно Эссенции! Баланс Эссенции: {user_crypto:.2f}"

    # Рассчитываем сумму возврата
    cursor.execute("SELECT balance FROM users WHERE id = 3")
    bought_before = 1000 - cursor.fetchone()['balance'] or 0  # Сколько было куплено до продажи

    total_refund = 0
    remaining_amount = amount

    # Цена уменьшается на 0.1 за каждую проданную единицу
    while remaining_amount > 0:
        current_chunk = min(1, remaining_amount)
        current_price = Decimal('1') + Decimal('0.08') * (bought_before - 1)  # Цена предыдущей единицы
        total_refund += current_price * current_chunk
        bought_before -= current_chunk
        remaining_amount -= current_chunk

    # Обновляем балансы
    cursor.execute(
        "UPDATE users SET balance_ar = balance_ar + %s, balance = balance - %s WHERE telegram_id = %s",
        (total_refund, amount, user_id))
    cursor.execute(
        "UPDATE users SET balance = balance + %s, balance_ar = balance_ar - %s WHERE id = 3",
        (amount,total_refund))
    connection.commit()
    cursor.close()
    connection.close()

    return f"Продано {amount:.2f} Эссенции за {total_refund:.2f} (средняя цена: {total_refund / amount:.2f})"


def handle_buy(bot):
    @bot.message_handler(commands=['buy'])
    def handle_buy1(message):
        try:
            amount_str = message.text.split()[1]
            amount = Decimal(amount_str).quantize(Decimal('0.00'))
            response = buy_crypto(message.from_user.id, amount)
            bot.reply_to(message, response)

        except:
            bot.reply_to(message, "Используйте: /buy [количество Эссенции]")


def handle_sell(bot):
    @bot.message_handler(commands=['sell'])
    def handle_sell1(message):
        try:
            amount_str = message.text.split()[1]
            amount = Decimal(amount_str).quantize(Decimal('0.00'))
            response = sell_crypto(message.from_user.id, amount)
            bot.reply_to(message, response)

        except:
            bot.reply_to(message, "Используйте: /sell [количество Эссенции]")


def handle_price(bot):
    @bot.message_handler(commands=['price'])
    def handle_price2(message):
        price = get_current_price()
        bot.reply_to(message, f"Текущая цена Эссенции: {price:.2f} Ар")
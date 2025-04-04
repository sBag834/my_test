import random
import time
import os

# Файл для текущего значения (обновляется каждую секунду)
CURRENT_NUMBER_FILE = "bot/current_number.txt"


def read_initial_number():
    try:
        if os.path.exists(CURRENT_NUMBER_FILE):
            with open(CURRENT_NUMBER_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return round(float(content), 2)
    except (ValueError, IOError) as e:
        print(f"Ошибка при чтении файла: {e}. Используется значение по умолчанию.")
    return 10.0  # Значение по умолчанию, если файл не существует или пуст


def main():
    number = read_initial_number()
    increase_chance = 50
    decrease_chance = 50

    try:
        while True:
            # Генерируем изменение
            change = random.uniform(0.05, 0.10)

            # Определяем, увеличивать или уменьшать
            total = increase_chance + decrease_chance
            rand_val = random.uniform(0, total)

            if rand_val < increase_chance:
                number += change
                increase_chance = max(0, increase_chance - 1)
                decrease_chance = 50
            else:
                number = max(0, number - change)
                decrease_chance = max(0, decrease_chance - 1)
                increase_chance = 50

            # Сохраняем текущее значение в файл (каждую секунду)
            with open(CURRENT_NUMBER_FILE, 'w') as f:
                f.write(f"{number:.2f}")

            # print(f"Число: {number:.2f}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("Программа остановлена.")


if __name__ == "__main__":
    main()
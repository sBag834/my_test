import subprocess
import sys
from threading import Thread

def run_file(file_path):
    """Запускает указанный Python-файл в отдельном процессе"""
    try:
        subprocess.run([sys.executable, file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске файла {file_path}: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")

def main():
    # Создаем потоки для каждого файла
    bot_thread = Thread(target=run_file, args=("bot.py",))
    internal_logic_thread = Thread(target=run_file, args=("internal_logic.py",))
    tg_bot = Thread(target=run_file, args=("bot/main.py",))

    # Запускаем потоки
    bot_thread.start()
    internal_logic_thread.start()
    tg_bot.start()

    # Ждем завершения потоков
    bot_thread.join()
    internal_logic_thread.join()
    tg_bot.join()

if __name__ == "__main__":
    print("Запуск bot.py и internal_logic.py...")
    main()
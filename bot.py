import discord
from discord.ext import commands
import os

# Настройки бота
TOKEN = 'MTM1NDI2NjQ4NjAyNTQ4NjM0Ng.Grf94D.op3BDJqHsO3zY7G9_T9l4-JfcYZFaUicoqMiaw'  # Замените на токен вашего бота
FILE_PATH = 'bot/current_number.txt'  # Путь к файлу с числом
COMMAND_PREFIX = '!'  # Префикс команд
COMMAND_NAME = 'cr'  # Название команды

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


@bot.event
async def on_ready():
    print(f'Бот {bot.user.name} готов к работе!')


@bot.command(name=COMMAND_NAME)
async def send_number(ctx):
    try:
        # Читаем число из файла
        with open(FILE_PATH, 'r') as file:
            number = file.read().strip()
        await ctx.send(f"Текущий курс Эссенции: {number}АР к 1 Эссенции")

    except Exception as e:
        await ctx.send(f"Произошла ошибка")

# Запуск бота
if __name__ == '__main__':
    bot.run(TOKEN)
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from bot.handlers.crypto_val import get_current_price

load_dotenv()

# Настройки бота
TOKEN = os.getenv('DS_BOT_TOKEN')  # Замените на токен вашего бота
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

        number = get_current_price()
        await ctx.send(f"Текущий курс Эссенции: {number:.2f}АР к 1 Эссенции")

    except Exception as e:
        await ctx.send(f"Произошла ошибка")

# Запуск бота
if __name__ == '__main__':
    bot.run(TOKEN)
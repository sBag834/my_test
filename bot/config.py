import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv('BOT_TOKEN')
    EXCHANGE_RATE_FILE = 'current_number.txt'
    DB_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
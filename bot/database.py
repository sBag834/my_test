from mysql.connector import Error
import mysql.connector
from decimal import Decimal, getcontext
from .config import Config

getcontext().prec = 10

def create_db_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            **Config.DB_CONFIG,
            autocommit=False
        )
        print("MySQL connection successful")
        return connection
    except Error as err:
        print(f"Database error: {err}")
        return None
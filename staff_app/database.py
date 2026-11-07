import os
import mysql.connector
from mysql.connector import Error
from tkinter import messagebox
import logging

# Configure logging
logging.basicConfig(
    filename='staff_app.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)
logger = logging.getLogger(__name__)

def create_db_connection():
    """Establish a connection to the database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "pizza_ordering_system"),
            collation="utf8mb4_unicode_ci",  # works on MySQL 8 and MariaDB
            charset='utf8mb4',
            use_unicode=True
        )
        if connection.is_connected():
            logger.info("Database connection established.")
            cursor = connection.cursor(dictionary=True, buffered=True)
            return connection, cursor
        else:
            raise Exception("Connection failed.")
    except Error as err:
        logger.error(f"Database Connection Error: {err}")
        messagebox.showerror("Database Connection Error", f"Error: {err}")
        return None, None

def close_connection(connection, cursor):
    """Close the database connection and cursor."""
    try:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            logger.info("Database connection closed.")
    except Error as err:
        logger.error(f"Connection Close Error: {err}")
        messagebox.showerror("Connection Close Error", f"Error closing connection: {err}")

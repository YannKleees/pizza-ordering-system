import os
import mysql.connector
from mysql.connector import Error
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        """Establish a connection to the database."""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "3306")),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "pizza_ordering_system"),
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",  # works on MySQL 8 and MariaDB
            )
            self.cursor = self.connection.cursor(dictionary=True, buffered=True)
            logger.info("Database connection established.")
        except Error as err:
            logger.error(f"Database Connection Error: {err}")
            raise

    def close(self):
        """Close the database connection and cursor."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("Database connection closed.")
        except Error as err:
            logger.error(f"Connection Close Error: {err}")
            raise

    def execute_query(self, query, params=None):
        """Execute a database query."""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor
        except Error as err:
            logger.error(f"Database Query Error: {err}")
            raise

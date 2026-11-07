import logging
from customer_app.database import DatabaseConnection
import datetime
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Customer:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash the password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def get_customer_by_username(self, username: str):
        """Retrieve customer details by username."""
        query = "SELECT * FROM customer WHERE username = %s"
        try:
            cursor = self.db.execute_query(query, (username,))
            customer = cursor.fetchone()
            if customer:
                logger.info(f"Customer '{username}' retrieved successfully.")
                return customer
            else:
                logger.warning(f"Customer '{username}' not found.")
                return None
        except Exception as e:
            logger.error(f"Error retrieving customer '{username}': {e}")
            return None

    def create_customer(self, user_details: dict) -> dict:
        """Create a new customer."""
        hashed_pw = self.hash_password(user_details['password'])
        query = """
            INSERT INTO customer (name, last_name, gender, birthdate, phone_number, address, username, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            user_details['name'],
            user_details['last_name'],
            user_details['gender'],
            user_details['birthdate'],
            user_details['phone_number'],
            user_details['address'],
            user_details['username'],
            hashed_pw
        )
        try:
            self.db.execute_query(query, params)
            self.db.connection.commit()
            logger.info(f"Customer '{user_details['username']}' created successfully.")
            return {"success": True, "message": "Registration successful."}
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"Error creating customer '{user_details['username']}': {e}")
            return {"success": False, "message": "Registration failed due to a database error."}

    def update_customer(self, customer_id: int, updated_details: dict) -> dict:
        """Update existing customer details."""
        query = """
            UPDATE customer
            SET name = %s, last_name = %s, gender = %s, birthdate = %s, phone_number = %s, address = %s
            WHERE customer_id = %s
        """
        params = (
            updated_details['name'],
            updated_details['last_name'],
            updated_details['gender'],
            updated_details['birthdate'],
            updated_details['phone_number'],
            updated_details['address'],
            customer_id
        )
        try:
            self.db.execute_query(query, params)
            self.db.connection.commit()
            logger.info(f"Customer ID '{customer_id}' updated successfully.")
            return {"success": True, "message": "Profile updated successfully."}
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"Error updating customer ID '{customer_id}': {e}")
            return {"success": False, "message": "Failed to update profile due to a database error."}

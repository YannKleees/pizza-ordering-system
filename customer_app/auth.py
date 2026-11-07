import logging
from customer_app.customer import Customer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Auth:
    def __init__(self, db):
        self.customer = Customer(db)

    def verify_login(self, username, password):
        """Verify login credentials for customers."""
        customer = self.customer.get_customer_by_username(username)
        if customer and customer['password'] == self.customer.hash_password(password):
            logger.info(f"User '{username}' logged in successfully.")
            return {"success": True, "customer_id": customer['customer_id']}
        else:
            logger.warning(f"Login failed for user '{username}'.")
            return {"success": False, "message": "Invalid username or password."}

    def register_user(self, user_details):
        """Register a new customer."""
        # Check if username already exists
        existing_customer = self.customer.get_customer_by_username(user_details['username'])
        if existing_customer:
            logger.warning(f"Registration failed: Username '{user_details['username']}' already exists.")
            return {"success": False, "message": "Username already exists."}

        # Create new customer
        return self.customer.create_customer(user_details)

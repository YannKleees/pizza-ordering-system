import logging
from decimal import Decimal, ROUND_HALF_UP
import datetime
import uuid

logger = logging.getLogger(__name__)

class OrderManager:
    def __init__(self, db):
        self.db = db

    def place_order(self, customer_id, basket, delivery_method, discount_code=None, is_birthday=False):
        """Place an order and apply discounts or free items if applicable."""
        try:
            # Menu prices are final; the basket subtracts the discounts (see Basket.calculate_total_price)
            subtotal = Decimal(str(basket.calculate_total_price()['subtotal']))

            # Birthday: 10% off, once per basket
            if is_birthday and not basket.birthday_discount_applied:
                basket.apply_discount(subtotal * Decimal('0.10'), "birthday")

            # A code typed at checkout that was not already applied in the basket
            if discount_code and basket.discount_code != discount_code:
                discount_result = self.validate_and_apply_discount_code(discount_code, subtotal)
                if not discount_result["success"]:
                    self.db.connection.rollback()
                    return {"success": False, "message": discount_result.get("message", "Discount application failed.")}
                basket.apply_discount(discount_result["discount_amount"])
                basket.discount_code = discount_code

            discount_amount = basket.discount_amount
            grand_total = Decimal(str(basket.calculate_total_price()['grand_total']))

            # Insert order into customerorder table
            insert_order_query = """
                INSERT INTO customerorder (customer_id, order_date, confirmation_number, status, total_price, delivery_method)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            confirmation_number = self.generate_confirmation_number()
            order_date = datetime.datetime.now()
            status = 'Pending'

            cursor = self.db.execute_query(insert_order_query, (
                customer_id,
                order_date,
                confirmation_number,
                status,
                float(grand_total),  # Ensure it's a float for the database
                delivery_method
            ))

            order_id = cursor.lastrowid  # Correct usage

            # Insert order items
            insert_order_item_query = """
                INSERT INTO order_item (order_id, menu_item_id, quantity, item_type)
                VALUES (%s, %s, %s, %s)
            """
            for item in basket.items:
                self.db.execute_query(insert_order_item_query, (
                    order_id,
                    item['id'],
                    item['quantity'],
                    item['type'].capitalize()   # without it every item was stored as 'Pizza' (enum default)
                ))
            
            # Commit the transaction
            self.db.connection.commit()

            # Update customer's loyalty points; every 10th pizza adds a free one to this order
            free_pizza_added = self.update_loyalty_points(customer_id, order_id, basket.items)

            # Prepare confirmation details
            details = {
                "confirmation_number": confirmation_number,
                "delivery_method": delivery_method,
                "total_price": grand_total,
                "delivery_time_estimation": self.estimate_delivery_time(delivery_method),
                "discount_applied": discount_amount > 0,
                "discount_amount": discount_amount,
                "free_pizza": bool(free_pizza_added)
            }


            return {"success": True, "details": details}

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            self.db.connection.rollback()
            return {"success": False, "message": "Failed to place order due to an unexpected error."}

    def get_free_pizza_id(self):
        """Retrieve the menu_item_id for the free pizza offer."""
        # A dedicated 'Free Pizza' item if the shop has one, otherwise the cheapest pizza on the menu
        query = """
            SELECT menu_item_id FROM menu_item
            WHERE type = 'Pizza'
            ORDER BY (name = 'Free Pizza') DESC, price ASC
            LIMIT 1
        """
        cursor = self.db.execute_query(query)
        result = cursor.fetchone()
        return result['menu_item_id'] if result else None
    
    def validate_and_apply_discount_code(self, discount_code, subtotal):
        """Validate the discount code and calculate the discount amount."""
        try:
            # Query the discount code from the database
            query = """
                SELECT discount_percentage, expiration_date, is_used
                FROM discountcode
                WHERE code = %s
            """
            cursor = self.db.execute_query(query, (discount_code,))
            discount = cursor.fetchone()

            if not discount:
                return {"success": False, "message": "Invalid discount code."}

            # Check if the discount code has expired
            expiration_date = discount['expiration_date']
            if expiration_date < datetime.date.today():
                return {"success": False, "message": "Discount code has expired."}

            # Check if the discount code has already been used
            if discount['is_used']:
                return {"success": False, "message": "Discount code has already been used."}

            # Apply the discount percentage to the subtotal
            discount_percentage = Decimal(str(discount['discount_percentage'])) / 100
            discount_amount = (subtotal * discount_percentage).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Mark the discount code as used in the database
            update_query = "UPDATE discountcode SET is_used = 1 WHERE code = %s"
            self.db.execute_query(update_query, (discount_code,))
            self.db.connection.commit()

            return {
                "success": True,
                "discount_amount": discount_amount,
                "message": "Discount applied successfully."
            }

        except Exception as e:
            logger.error(f"Error validating discount code: {e}")
            self.db.connection.rollback()
            return {"success": False, "message": "An error occurred during discount code validation."}

    def get_free_drink_id(self):
        """Retrieve the menu_item_id for the free drink offer."""
        # Assuming you have a special menu item for the free drink
        query = "SELECT menu_item_id FROM menu_item WHERE name = 'Free Drink' LIMIT 1"
        cursor = self.db.execute_query(query)
        result = cursor.fetchone()
        return result['menu_item_id'] if result else None

    def generate_confirmation_number(self):
        """Generate a unique confirmation number for the order."""
        return uuid.uuid4().hex[:8].upper()

    def update_loyalty_points(self, customer_id, order_id, items):
        """Update the customer's loyalty points based on the items ordered."""
        # Count the number of pizzas ordered in this order
        pizzas_ordered_in_order = 0
        for item in items:
            if item['type'].lower() == 'pizza':
                pizzas_ordered_in_order += item['quantity']
        if pizzas_ordered_in_order == 0:
            return False  # No pizzas ordered, nothing to update

        try:
            # Get the current pizzas_ordered count from the database
            query = "SELECT pizzas_ordered FROM customer WHERE customer_id = %s"
            cursor = self.db.execute_query(query, (customer_id,))
            result = cursor.fetchone()
            if result is None:
                logger.error(f"Customer with ID {customer_id} not found.")
                return False

            current_pizzas_ordered = result['pizzas_ordered'] or 0

            # Update the pizzas_ordered count
            new_pizzas_ordered = current_pizzas_ordered + pizzas_ordered_in_order

            free_pizza_added = False

            # Check if customer qualifies for a free pizza
            if new_pizzas_ordered >= 10:
                free_pizza_added = True
                new_pizzas_ordered = new_pizzas_ordered % 10  # Reset count after giving free pizza

                # Add a free pizza to the order
                free_pizza_id = self.get_free_pizza_id()
                if free_pizza_id:
                    insert_order_item_query = """
                        INSERT INTO order_item (order_id, menu_item_id, quantity, item_type)
                        VALUES (%s, %s, %s, 'Pizza')
                    """
                    self.db.execute_query(insert_order_item_query, (
                        order_id,
                        free_pizza_id,
                        1
                    ))
                    logger.info(f"Added free pizza to order {order_id} for customer {customer_id}")
                else:
                    logger.warning("Free pizza ID not found. Cannot add free pizza to the order.")

            # Update the customer's pizzas_ordered count in the database
            update_query = "UPDATE customer SET pizzas_ordered = %s WHERE customer_id = %s"
            self.db.execute_query(update_query, (new_pizzas_ordered, customer_id))
            self.db.connection.commit()

            return free_pizza_added

        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"Error updating loyalty points for customer {customer_id}: {e}")
            return False

    def estimate_delivery_time(self, delivery_method):
        """Estimate delivery time based on the delivery method."""
        if delivery_method == 'Delivery':
            return "30 minutes"
        else:
            return "Your order is ready for pickup in 15 minutes"

    def cancel_order(self, customer_id, order_id):
        """Cancel the order if it's still pending."""
        try:
            # Check if the order is still 'Pending'
            query = """
                SELECT status FROM customerorder WHERE customer_id = %s AND order_id = %s
            """
            cursor = self.db.execute_query(query, (customer_id, order_id))
            order = cursor.fetchone()

            if not order:
                return {"success": False, "message": "Order not found."}

            if order['status'] != 'Pending':
                return {"success": False, "message": "Order cannot be cancelled because it is no longer pending."}

            # Cancel the order
            update_query = """
                UPDATE customerorder SET status = 'Cancelled' WHERE order_id = %s AND customer_id = %s
            """
            self.db.execute_query(update_query, (order_id, customer_id))
            self.db.connection.commit()

            return {"success": True, "message": "Order has been successfully cancelled."}

        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"Error cancelling order: {e}")
            return {"success": False, "message": "An error occurred while trying to cancel the order."}

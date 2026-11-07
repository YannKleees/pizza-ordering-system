import logging
from decimal import Decimal, ROUND_HALF_UP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Basket:
    def __init__(self):
        self.items = []  # List of items: [{'id': ..., 'name': ..., 'quantity': ..., 'type': ..., 'price': ...}, ...]
        self.discount_amount = Decimal('0.00')  # Initialize total discount to zero
        self.birthday_discount_applied = False  # Flag to track if birthday discount has been applied

    def add_item(self, item_id, name, quantity, item_type, price):
        """Add an item to the basket."""
        for item in self.items:
            if item['id'] == item_id:
                item['quantity'] += quantity
                logger.info(f"Updated '{name}' quantity to {item['quantity']}.")
                return
        # Ensure price is a Decimal for precise calculations
        price_decimal = Decimal(str(price)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.items.append({
            'id': item_id,
            'name': name,
            'quantity': quantity,
            'type': item_type,
            'price': price_decimal
        })
        logger.info(f"Added '{name}' to basket with quantity {quantity} at price €{price_decimal:.2f} each.")

    def remove_item(self, item_id):
        """Remove an item from the basket."""
        for item in self.items:
            if item['id'] == item_id:
                self.items.remove(item)
                logger.info(f"Removed '{item['name']}' from basket.")
                return True
        logger.warning(f"Item with ID {item_id} not found in basket.")
        return False

    def clear_basket(self):
        """Clear all items and discounts from the basket."""
        self.items = []
        self.discount_amount = Decimal('0.00')
        self.birthday_discount_applied = False
        logger.info("Basket cleared.")

    def apply_discount(self, discount_amount, discount_type="general"):
        """
        Apply a discount to the basket.

        Parameters:
            discount_amount (Decimal or float): The discount amount to apply.
            discount_type (str): The type of discount ('general', 'birthday', etc.)
        """
        try:
            discount_amount = Decimal(str(discount_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if discount_amount < Decimal('0.00'):
                logger.warning("Attempted to apply a negative discount. Resetting to zero.")
                discount_amount = Decimal('0.00')
            
            if discount_type == "birthday":
                if not self.birthday_discount_applied:
                    self.discount_amount += discount_amount
                    self.birthday_discount_applied = True
                    logger.info(f"Applied {discount_type} discount: €{discount_amount:.2f}")
            else:
                self.discount_amount += discount_amount
                logger.info(f"Applied {discount_type} discount: €{discount_amount:.2f}")
        except Exception as e:
            logger.error(f"Error applying discount: {e}")
            self.discount_amount = Decimal('0.00')

    def calculate_total_price(self):
        """
        Calculate the total price of items in the basket, apply VAT and profit margin,
        and subtract any discounts.
        Returns a dictionary with detailed cost breakdown.
        """
        subtotal = Decimal('0.00')
        
        for item in self.items:
            item_total = item['price'] * item['quantity']
            subtotal += item_total

        # Apply VAT (assuming 9%)
        VAT_RATE = Decimal('0.09')
        vat_amount = (subtotal * VAT_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Apply 40% profit margin
        PROFIT_MARGIN = Decimal('0.40')
        profit = (subtotal * PROFIT_MARGIN).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Calculate grand total: subtotal + VAT + profit
        grand_total = (subtotal + vat_amount + profit).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Apply discount if any
        grand_total_after_discount = (grand_total - self.discount_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        grand_total_after_discount = max(Decimal('0.00'), grand_total_after_discount)

        logger.info(f"Subtotal: €{subtotal:.2f}")
        logger.info(f"VAT (9%): €{vat_amount:.2f}")
        logger.info(f"Profit Margin (40%): €{profit:.2f}")
        logger.info(f"Grand Total before discount: €{grand_total:.2f}")
        logger.info(f"Discount Applied: €{self.discount_amount:.2f}")
        logger.info(f"Grand Total after discount: €{grand_total_after_discount:.2f}")

        return {
            'subtotal': subtotal,
            'vat_amount': vat_amount,
            'profit': profit,
            'grand_total': grand_total_after_discount
        }

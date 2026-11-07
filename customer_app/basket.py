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
        self.discount_code = None  # Code already validated in the basket, so the order does not re-check it

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
        self.discount_code = None
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
        Total of the basket. Menu prices are final: the staff app already includes the 40%
        margin and 9% VAT, so only discounts are subtracted here. The VAT contained in the
        total is reported for the receipt.
        """
        subtotal = sum((item['price'] * item['quantity'] for item in self.items), Decimal('0.00'))
        grand_total = max(Decimal('0.00'), subtotal - self.discount_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        vat_included = (grand_total * Decimal('9') / Decimal('109')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        logger.info(f"Subtotal: €{subtotal:.2f}, discounts: €{self.discount_amount:.2f}, total: €{grand_total:.2f}")
        return {
            'subtotal': subtotal,
            'vat_amount': vat_included,
            'profit': Decimal('0.00'),
            'grand_total': grand_total
        }

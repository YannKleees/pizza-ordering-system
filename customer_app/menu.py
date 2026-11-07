import logging
import decimal

# Configure logging
logger = logging.getLogger(__name__)

class Menu:
    def __init__(self, db):
        self.db = db
        self.menu = {}  # Structure: {menu_item_id: {details}}

    def fetch_menu(self):
        """Fetch all menu items with ingredients and dietary info."""
        try:
            # Corrected SQL Query
            items_query = """
                SELECT mi.menu_item_id, mi.name, mi.type, mi.price,
                    i.name AS ingredient_name, i.is_vegetarian AS ingredient_is_vegetarian, i.is_vegan AS ingredient_is_vegan, i.cost,
                    p.is_vegetarian AS pizza_is_vegetarian, p.is_vegan AS pizza_is_vegan
                FROM menu_item mi
                LEFT JOIN pizza p ON mi.menu_item_id = p.pizza_id
                LEFT JOIN pizza_ingredient pi ON p.pizza_id = pi.pizza_id
                LEFT JOIN ingredient i ON pi.ingredient_id = i.ingredient_id
            """
            cursor = self.db.execute_query(items_query)
            items = cursor.fetchall()

            for item in items:
                menu_item_id = item['menu_item_id']
                if menu_item_id not in self.menu:
                    self.menu[menu_item_id] = {
                        'name': item['name'],
                        'type': item['type'],
                        'ingredients': [],
                        'is_vegetarian': item['pizza_is_vegetarian'],
                        'is_vegan': item['pizza_is_vegan'],
                        'ingredient_costs': [],
                        'price': float(item['price']) if item['price'] else 0.00
                    }
                if item['ingredient_name']:
                    self.menu[menu_item_id]['ingredients'].append(item['ingredient_name'])
                    self.menu[menu_item_id]['ingredient_costs'].append(float(item['cost']))
                    # Update dietary flags based on ingredients
                    if not item['ingredient_is_vegetarian']:
                        self.menu[menu_item_id]['is_vegetarian'] = 0
                    if not item['ingredient_is_vegan']:
                        self.menu[menu_item_id]['is_vegan'] = 0

            logger.info("Menu data fetched and dietary information updated successfully.")
        except Exception as e:
            logger.error(f"Error fetching menu data: {e}", exc_info=True)


    def get_existing_price(self, name, item_type):
        """Fetch existing price for non-pizza items."""
        query = "SELECT price FROM menu_item WHERE name = %s AND type = %s"
        cursor = self.db.execute_query(query, (name, item_type))
        result = cursor.fetchone()
        if result:
            return float(result['price'])
        else:
            return 0.00

    def get_menu_items_by_type(self, item_type):
        """Retrieve menu items based on their type."""
        items = {}
        for menu_item_id, details in self.menu.items():
            if details['type'].lower() == item_type.lower():
                items[menu_item_id] = details
        return items

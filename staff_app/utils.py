from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_menu_item_details(menu_item_id, cursor):
    """
    Get the name, price, and type of the menu item from the menu_item table.
    """
    try:
        cursor.execute("SELECT name, price, type FROM menu_item WHERE menu_item_id = %s", (menu_item_id,))
        result = cursor.fetchone()
        if result:
            return result['name'], float(result['price']), result['type']
        else:
            logger.warning(f"Menu item ID {menu_item_id} not found.")
            return "Unknown Item", 0.00, "Unknown"
    except Exception as e:
        logger.error(f"Error fetching menu item details: {e}")
        return "Unknown Item", 0.00, "Unknown"

def convert_to_datetime(date_value):
    """
    Convert a date value to a datetime object.
    """
    if isinstance(date_value, datetime):
        return date_value
    elif isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            logger.error(f"Failed to parse date string '{date_value}': {e}")
            return datetime.now()
    else:
        logger.warning(f"Unknown date format: {date_value}. Setting to current datetime.")
        return datetime.now()

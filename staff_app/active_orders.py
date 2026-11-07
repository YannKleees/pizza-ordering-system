import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import ttk
from .utils import get_menu_item_details, convert_to_datetime  # Import the utility functions
import decimal
import logging

logger = logging.getLogger(__name__)

class ActiveOrders:
    def __init__(self, parent, cursor, connection):
        self.parent = parent
        self.cursor = cursor
        self.connection = connection
        self.setup_ui()

    def setup_ui(self):
        """Initialize the Active Orders UI components."""
        # Create a frame for controls
        controls_frame = ttk.Frame(self.parent)
        controls_frame.pack(fill='x', pady=10, padx=10)

        # Refresh Button
        refresh_button = ttk.Button(controls_frame, text="Refresh Orders", bootstyle="info",
                                    command=self.populate_active_orders)
        refresh_button.pack(side='right', padx=10)

        # Create a Treeview to display orders
        columns = ("Order ID", "Order Date", "Delivery Method", "Status", "Customer Name", "Address", "Total Price")
        self.tree = ttk.Treeview(self.parent, columns=columns, show='headings', selectmode='browse')
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Address":
                self.tree.column(col, anchor='center', width=200)
            else:
                self.tree.column(col, anchor='center')

        # Add scrollbar to the Treeview
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        # Advance Order Status Button
        advance_button = ttk.Button(self.parent, text="Advance Selected Order Status", bootstyle="success",
                                    command=self.advance_order_status)
        advance_button.pack(pady=10)

        # Populate orders
        self.populate_active_orders()

    def fetch_active_orders(self):
        """Fetch all active orders that are not completed, delivered, or cancelled."""
        try:
            self.cursor.execute("""
                SELECT co.order_id, co.order_date, co.delivery_method, co.status, c.name, c.address
                FROM customerorder co
                JOIN customer c ON co.customer_id = c.customer_id
                WHERE co.status NOT IN ('Completed', 'Delivered', 'Cancelled', 'Dispatched')
                ORDER BY co.order_date ASC
            """)
            orders = self.cursor.fetchall()
            logger.info(f"Fetched {len(orders)} active orders.")
            return orders
        except Exception as e:
            logger.error(f"Failed to fetch active orders: {e}")
            messagebox.showerror("Database Error", f"Failed to fetch active orders: {e}")
            return []

    # Define the functions to fetch item details for Pizza, Drink, and Dessert
def get_menu_item_details_from_pizza(menu_item_id, cursor):
    """Fetch details for a pizza."""
    try:
        cursor.execute("SELECT name, base_price FROM Pizza WHERE pizza_id = %s", (menu_item_id,))
        result = cursor.fetchone()
        if result:
            return result['name'], float(result['base_price'])
    except Exception as e:
        print(f"Error fetching pizza details: {e}")
    return "Unknown Item", 0.00

def get_menu_item_details_from_drink(menu_item_id, cursor):
    """Fetch details for a drink."""
    try:
        cursor.execute("SELECT name, price FROM Drink WHERE drink_id = %s", (menu_item_id,))
        result = cursor.fetchone()
        if result:
            return result['name'], float(result['price'])
    except Exception as e:
        print(f"Error fetching drink details: {e}")
    return "Unknown Item", 0.00

def get_menu_item_details_from_dessert(menu_item_id, cursor):
    """Fetch details for a dessert."""
    try:
        cursor.execute("SELECT name, price FROM Dessert WHERE dessert_id = %s", (menu_item_id,))
        result = cursor.fetchone()
        if result:
            return result['name'], float(result['price'])
    except Exception as e:
        print(f"Error fetching dessert details: {e}")
    return "Unknown Item", 0.00

# Now use these functions in fetch_order_items
def fetch_order_items(self, order_id):
    """Fetch items associated with a specific order."""
    try:
        # Fetch the item ID and quantity for each order item
        self.cursor.execute("""
            SELECT oi.menu_item_id, oi.quantity
            FROM order_item oi
            WHERE oi.order_id = %s
        """, (order_id,))
        items = self.cursor.fetchall()
        order_items = []

        for item in items:
            menu_item_id = item['menu_item_id']
            quantity = item['quantity']
            
            # Attempt to fetch from Pizza table
            name, price = get_menu_item_details_from_pizza(menu_item_id, self.cursor)
            if name == "Unknown Item":
                # If not found in Pizza, try Drink table
                name, price = get_menu_item_details_from_drink(menu_item_id, self.cursor)
            if name == "Unknown Item":
                # If not found in Drink, try Dessert table
                name, price = get_menu_item_details_from_dessert(menu_item_id, self.cursor)

            order_items.append({'name': name, 'quantity': quantity, 'price': price})
        
        return order_items
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to fetch order items: {e}")
        return []



    def calculate_total_price(self, order_id):
        """Calculate the total price for a specific order."""
        try:
            items = self.fetch_order_items(order_id)
            total_price = sum(decimal.Decimal(item['price']) * item['quantity'] for item in items)
            return total_price.quantize(decimal.Decimal('0.01'))
        except Exception as e:
            logger.error(f"Failed to calculate total price for Order ID {order_id}: {e}")
            messagebox.showerror("Calculation Error", f"Failed to calculate total price: {e}")
            return decimal.Decimal('0.00')

    def populate_active_orders(self):
        """Populate the Active Orders tab with current orders."""
        # Clear existing entries
        for item in self.tree.get_children():
            self.tree.delete(item)

        orders = self.fetch_active_orders()

        for order in orders:
            order_id = order['order_id']
            order_date = convert_to_datetime(order['order_date'])
            delivery_method = order['delivery_method']
            status = order['status']
            customer_name = order['name']
            customer_address = order['address']

            total_price = self.calculate_total_price(order_id)

            self.tree.insert("", tk.END, values=(
                order_id,
                order_date.strftime("%Y-%m-%d %H:%M:%S"),
                delivery_method,
                status,
                customer_name,
                customer_address,
                f"€{total_price}"
            ))

    def advance_order_status(self):
        """Advance the status of the selected order to the next stage."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select an order to advance its status.")
            return

        order_values = self.tree.item(selected[0])['values']
        order_id = order_values[0]
        current_status = order_values[3]

        status_sequence = ['Pending', 'Preparing', 'Cooking', 'Ready for Delivery', 'Out for Delivery', 'Dispatched', 'Delivered', 'Completed']
        if current_status not in status_sequence:
            messagebox.showerror("Error", f"Unknown current status '{current_status}' for Order ID {order_id}.")
            return

        current_index = status_sequence.index(current_status)
        if current_index + 1 >= len(status_sequence):
            messagebox.showinfo("Info", f"Order ID {order_id} is already at the final status '{current_status}'.")
            return

        next_status = status_sequence[current_index + 1]

        try:
            self.cursor.execute("UPDATE customerorder SET status = %s WHERE order_id = %s", (next_status, order_id))
            self.connection.commit()
            messagebox.showinfo("Success", f"Order ID {order_id} status updated to '{next_status}'.")
            logger.info(f"Order ID {order_id} status updated from '{current_status}' to '{next_status}'.")
            self.populate_active_orders()
        except Exception as e:
            logger.error(f"Failed to advance order status for Order ID {order_id}: {e}")
            messagebox.showerror("Database Error", f"Failed to advance order status: {e}")

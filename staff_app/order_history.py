import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import ttk
from .utils import get_menu_item_details, convert_to_datetime
import logging

logger = logging.getLogger(__name__)

class OrderHistory:
    def __init__(self, parent, cursor):
        self.parent = parent
        self.cursor = cursor
        self.setup_ui()

    def setup_ui(self):
        """Initialize the Order History UI components."""
        # Clear any existing content in the parent frame
        for widget in self.parent.winfo_children():
            widget.destroy()

        self.parent.pack(fill='both', expand=True)
        ttk.Label(self.parent, text="Order History", font=("Helvetica", 18, "bold")).pack(pady=10)

        # Create a Treeview to display orders
        columns = ("Order ID", "Order Date", "Customer Name", "Total Price", "Status")
        self.tree = ttk.Treeview(self.parent, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center')

        # Add scrollbar to the Treeview
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        # Populate orders
        self.populate_orders()

        # Bind double-click event to show order details
        self.tree.bind("<Double-1>", self.show_order_details)

    def populate_orders(self):
        """Fetch and display past orders."""
        try:
            self.cursor.execute("""
                SELECT co.order_id, co.order_date, c.name AS customer_name, co.total_price, co.status
                FROM customerorder co
                JOIN customer c ON co.customer_id = c.customer_id
                ORDER BY co.order_date DESC
            """)
            orders = self.cursor.fetchall()

            # Clear existing entries
            for item in self.tree.get_children():
                self.tree.delete(item)

            for order in orders:
                order_id = order['order_id']
                order_date = convert_to_datetime(order['order_date']).strftime("%Y-%m-%d %H:%M:%S")
                customer_name = order['customer_name']
                total_price = f"€{order['total_price']:.2f}"
                status = order['status']

                self.tree.insert("", tk.END, values=(
                    order_id,
                    order_date,
                    customer_name,
                    total_price,
                    status
                ))
        except Exception as e:
            logger.error(f"Failed to fetch order history: {e}")
            messagebox.showerror("Database Error", f"Failed to fetch order history: {e}")

    def fetch_order_items(self, order_id):
        """Fetch items associated with a specific order."""
        try:
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
                name, price, item_type = get_menu_item_details(menu_item_id, self.cursor)
                order_items.append({'name': name, 'quantity': quantity, 'price': price})
            logger.info(f"Fetched {len(order_items)} items for Order ID {order_id}.")
            return order_items
        except Exception as e:
            logger.error(f"Failed to fetch order items for Order ID {order_id}: {e}")
            messagebox.showerror("Database Error", f"Failed to fetch order items: {e}")
            return []

    def show_order_details(self, event):
        """Display the details of the selected order."""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        order_id = self.tree.item(selected_item)['values'][0]
        order_items = self.fetch_order_items(order_id)

        details_window = tk.Toplevel(self.parent)
        details_window.title(f"Order Details - Order ID {order_id}")
        details_window.geometry("400x300")

        ttk.Label(details_window, text=f"Order ID: {order_id}", font=("Helvetica", 14, "bold")).pack(pady=10)

        # Display order items
        for item in order_items:
            item_text = f"{item['quantity']} x {item['name']} @ €{item['price']:.2f} each"
            ttk.Label(details_window, text=item_text).pack(anchor='w', padx=20)

    def refresh(self):
        """Refresh the order history."""
        self.populate_orders()

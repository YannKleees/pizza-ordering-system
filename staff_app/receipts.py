import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import ttk
from .utils import get_menu_item_details, convert_to_datetime
import logging

logger = logging.getLogger(__name__)

class Receipts:
    def __init__(self, parent, cursor):
        self.parent = parent
        self.cursor = cursor
        self.setup_ui()

    def setup_ui(self):
        """Initialize the Receipts UI components."""
        # Clear any existing content in the parent frame
        for widget in self.parent.winfo_children():
            widget.destroy()

        self.parent.pack(fill='both', expand=True)
        ttk.Label(self.parent, text="Receipts", font=("Helvetica", 18, "bold")).pack(pady=10)

        # Create a frame for Treeview and scrollbar
        tree_frame = ttk.Frame(self.parent)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Define columns
        columns = ("Order ID", "Order Date", "Customer Name", "Total Price", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        # Define headings
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Customer Name":
                self.tree.column(col, anchor='center', width=150)
            else:
                self.tree.column(col, anchor='center', width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Position Treeview and scrollbar
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Populate orders
        self.populate_orders()

        # Bind double-click event to generate receipt
        self.tree.bind("<Double-1>", self.generate_receipt)

    def populate_orders(self):
        """Fetch and display orders that need receipts."""
        try:
            self.cursor.execute("""
                SELECT co.order_id, co.order_date, c.name AS customer_name, co.total_price, co.status
                FROM customerorder co
                JOIN customer c ON co.customer_id = c.customer_id
                WHERE co.status = 'Delivered'
                ORDER BY co.order_date DESC
            """)
            orders = self.cursor.fetchall()

            # Clear existing entries
            for item in self.tree.get_children():
                self.tree.delete(item)

            if not orders:
                ttk.Label(self.parent, text="No delivered orders available for receipts.", font=("Helvetica", 12)).pack(pady=10)
                return

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

            logger.info(f"Fetched {len(orders)} delivered orders for receipts.")

        except Exception as e:
            logger.error(f"Failed to fetch receipts: {e}")
            messagebox.showerror("Database Error", f"Failed to fetch receipts: {e}")

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

    def generate_receipt(self, event):
        """Generate and display the receipt for the selected order."""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        order_id = self.tree.item(selected_item)['values'][0]
        order_items = self.fetch_order_items(order_id)

        if not order_items:
            messagebox.showwarning("No Items", f"No items found for Order ID {order_id}.")
            return

        receipt_window = tk.Toplevel(self.parent)
        receipt_window.title(f"Receipt - Order ID {order_id}")
        receipt_window.geometry("400x500")

        ttk.Label(receipt_window, text=f"Receipt - Order ID {order_id}", font=("Helvetica", 14, "bold")).pack(pady=10)

        # Display order items
        total_price = 0
        for item in order_items:
            item_total = item['quantity'] * item['price']
            total_price += item_total
            item_text = f"{item['quantity']} x {item['name']} @ €{item['price']:.2f} each = €{item_total:.2f}"
            ttk.Label(receipt_window, text=item_text).pack(anchor='w', padx=20)

        ttk.Label(receipt_window, text=f"Total: €{total_price:.2f}", font=("Helvetica", 12, "bold")).pack(pady=10)

        # Optionally, add a button to save the receipt as a text file or PDF
        def save_receipt():
            try:
                import os
                receipt_text = f"Receipt - Order ID {order_id}\n\n"
                for item in order_items:
                    receipt_text += f"{item['quantity']} x {item['name']} @ €{item['price']:.2f} each = €{item['quantity'] * item['price']:.2f}\n"
                receipt_text += f"\nTotal: €{total_price:.2f}"

                # Save to a text file
                file_path = f"receipt_order_{order_id}.txt"
                with open(file_path, "w") as f:
                    f.write(receipt_text)

                messagebox.showinfo("Success", f"Receipt saved as {os.path.abspath(file_path)}.")
            except Exception as e:
                logger.error(f"Failed to save receipt: {e}")
                messagebox.showerror("Error", f"Failed to save receipt: {e}")

        save_button = ttk.Button(receipt_window, text="Save Receipt", bootstyle="success", command=save_receipt)
        save_button.pack(pady=20)

    def refresh(self):
        """Refresh the receipts."""
        self.populate_orders()

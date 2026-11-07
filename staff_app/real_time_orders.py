import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import ttk
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RealTimeOrders:
    def __init__(self, parent, cursor, connection):
        self.parent = parent
        self.cursor = cursor
        self.connection = connection
        self.setup_ui()
        # Start any necessary periodic updates
        # self.schedule_updates()  # If applicable

    def setup_ui(self):
        """Initialize the Real-Time Orders UI components."""
        self.parent.pack(fill='both', expand=True)
        
        # Controls Frame
        controls_frame = ttk.Frame(self.parent)
        controls_frame.pack(fill='x', pady=10, padx=10)
        
        # Existing Buttons (e.g., Refresh)
        refresh_button = ttk.Button(
            controls_frame,
            text="Refresh",
            bootstyle="info",
            command=self.populate_orders
        )
        refresh_button.pack(side='left', padx=5)
        
        # **Continue Order State Button**
        continue_state_button = ttk.Button(
            controls_frame,
            text="Continue Order State",
            bootstyle="primary",
            command=self.continue_order_state
        )
        continue_state_button.pack(side='left', padx=5)
        
        # Treeview to display real-time orders
        columns = ("Order ID", "Order Date", "Customer Name", "Address", "Status")
        self.tree = ttk.Treeview(self.parent, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Address":
                self.tree.column(col, anchor='center', width=200)
            else:
                self.tree.column(col, anchor='center', width=150)

        # Add scrollbar to the Treeview
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        
        self.tree.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Populate orders
        self.populate_orders()

    def populate_orders(self):
        """Fetch and display real-time orders."""
        try:
            # Fetch all orders with status 'Pending' or 'Ready for Delivery'
            self.cursor.execute("""
                SELECT co.order_id, co.order_date, c.name AS customer_name, c.address, co.status
                FROM customerorder co
                JOIN customer c ON co.customer_id = c.customer_id
                WHERE co.status IN ('Pending', 'Ready for Delivery')
                ORDER BY co.order_date DESC
            """)
            orders = self.cursor.fetchall()

            logger.info(f"Fetched {len(orders)} real-time orders.")

            # Clear existing entries
            for item in self.tree.get_children():
                self.tree.delete(item)

            if not orders:
                ttk.Label(self.parent, text="No real-time orders available.", font=("Helvetica", 12)).pack(pady=10)
                return

            for order in orders:
                order_id = order['order_id']
                order_date = order['order_date'].strftime('%Y-%m-%d %H:%M:%S')
                customer_name = order['customer_name']
                address = order['address']
                status = order['status']

                # Insert the order details into the Treeview
                self.tree.insert("", tk.END, values=(
                    order_id,
                    order_date,
                    customer_name,
                    address,
                    status
                ))

        except Exception as e:
            logger.error(f"Failed to fetch real-time orders: {e}")
            messagebox.showerror("Database Error", f"Failed to fetch real-time orders: {e}")

    def continue_order_state(self):
        """Continue the state of selected orders."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Selection Error", "Please select at least one order to continue its state.")
            return

        try:
            for item in selected_items:
                order_id = self.tree.item(item)['values'][0]
                current_status = self.tree.item(item)['values'][4]  # 'Status' column

                # Determine the next status based on current status
                next_status = self.get_next_status(current_status)
                if not next_status:
                    logger.warning(f"Order ID {order_id} has an invalid or final status: {current_status}")
                    messagebox.showwarning("Status Warning", f"Order ID {order_id} has an invalid or final status: {current_status}")
                    continue

                # Update order status in the database
                self.cursor.execute("""
                    UPDATE customerorder 
                    SET status = %s 
                    WHERE order_id = %s
                """, (next_status, order_id))
                logger.info(f"Order ID {order_id} status updated from '{current_status}' to '{next_status}'.")

            # Commit the changes after all updates
            self.connection.commit()
            messagebox.showinfo("Success", "Selected orders have been updated to the next state.")
            logger.info(f"Successfully updated {len(selected_items)} orders to the next state.")

        except Exception as e:
            # Rollback in case of any error during the update
            self.connection.rollback()
            logger.error(f"Failed to continue order states: {e}")
            messagebox.showerror("Database Error", f"Failed to continue order states: {e}")

        # Refresh the Treeview to reflect updated statuses
        self.populate_orders()

    def get_next_status(self, current_status):
        """Determine the next status based on the current status."""
        status_flow = {
            "Pending": "Ready for Delivery",
            "Ready for Delivery": "Delivered",
            # "Delivered" and "Cancelled" are terminal states
        }
        return status_flow.get(current_status)

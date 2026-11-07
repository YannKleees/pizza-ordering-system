import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import ttk
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)

class DeliveryManagement:
    def __init__(self, parent, cursor, connection):
        self.parent = parent
        self.cursor = cursor
        self.connection = connection
        self.setup_ui()
        # Start periodic updates for delivery personnel availability
        self.schedule_availability_update()
    
    def setup_ui(self):
        """Initialize the Delivery Management UI components."""
        self.parent.pack(fill='both', expand=True)
        
        # Controls Frame
        controls_frame = ttk.Frame(self.parent)
        controls_frame.pack(fill='x', pady=10, padx=10)
        
        # Assign Delivery Button
        assign_button = ttk.Button(
            controls_frame,
            text="Assign Delivery Personnel",
            bootstyle="success",
            command=self.assign_delivery_personnel
        )
        assign_button.pack(side='left', padx=5)
        
        # Manage Personnel Button
        manage_button = ttk.Button(
            controls_frame,
            text="Manage Personnel",
            bootstyle="primary",
            command=self.manage_delivery_personnel
        )
        manage_button.pack(side='left', padx=5)
        
        # Mark as Ready for Delivery Button
        mark_ready_button = ttk.Button(
            controls_frame,
            text="Mark as Ready for Delivery",
            bootstyle="warning",
            command=self.mark_as_ready_for_delivery
        )
        mark_ready_button.pack(side='left', padx=5)
        
        # Mark as Delivered Button
        mark_delivered_button = ttk.Button(
            controls_frame,
            text="Mark as Delivered",
            bootstyle="warning",
            command=self.mark_as_delivered
        )
        mark_delivered_button.pack(side='left', padx=5)
        
        # Refresh Button
        refresh_button = ttk.Button(
            controls_frame,
            text="Refresh",
            bootstyle="info",
            command=self.populate_orders
        )
        refresh_button.pack(side='left', padx=5)
        
        # Treeview to display orders needing delivery assignment
        columns = ("Order ID", "Order Date", "Customer Name", "Address", "Status", "Delivery Person")
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
    
    def extract_postal_code(self, address):
        """Extract postal code from address using regex."""
        # Assuming postal codes are 4-digit numbers
        match = re.search(r'\b\d{4}\b', address)
        if match:
            postal_code = match.group()
            logger.info(f"Extracted postal code '{postal_code}' from address '{address}'.")
            return postal_code
        else:
            logger.warning(f"No valid postal code found in address: '{address}'")
            return 'Unknown'
    
    def populate_orders(self):
        """Fetch and display orders needing delivery assignment, including already assigned orders."""
        try:
            # Fetch orders that are 'Pending', 'Ready for Delivery', or 'Out for Delivery'
            self.cursor.execute("""
                SELECT co.order_id, co.order_date, c.name AS customer_name, c.address, co.status,
                    dp.name AS delivery_person_name
                FROM customerorder co
                JOIN customer c ON co.customer_id = c.customer_id
                LEFT JOIN deliveryassignment da ON co.order_id = da.order_id
                LEFT JOIN deliverypersonnel dp ON da.delivery_person_id = dp.delivery_person_id
                WHERE co.status IN ('Pending', 'Ready for Delivery', 'Out for Delivery')
                ORDER BY co.order_date ASC
            """)
            orders = self.cursor.fetchall()

            logger.info(f"Fetched {len(orders)} orders with status 'Pending', 'Ready for Delivery', or 'Out for Delivery'.")

            # Clear existing entries
            for item in self.tree.get_children():
                self.tree.delete(item)

            if not orders:
                ttk.Label(self.parent, text="No orders available for delivery assignment.", font=("Helvetica", 12)).pack(pady=10)
                return

            for order in orders:
                order_id = order['order_id']
                order_date = order['order_date'].strftime('%Y-%m-%d %H:%M:%S')
                customer_name = order['customer_name']
                address = order['address']
                status = order['status']
                delivery_person_name = order['delivery_person_name'] if order['delivery_person_name'] else 'Unassigned'

                # Insert the order details into the Treeview
                self.tree.insert("", tk.END, values=(
                    order_id,
                    order_date,
                    customer_name,
                    address,
                    status,
                    delivery_person_name  # Display the delivery person's name
                ))

        except Exception as e:
            logger.error(f"Failed to fetch orders: {e}")
            messagebox.showerror("Database Error", f"Failed to fetch orders: {e}")

    def mark_as_ready_for_delivery(self):
        """Mark selected orders as 'Ready for Delivery'."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Selection Error", "Please select at least one order to mark as ready for delivery.")
            return

        try:
            for item in selected_items:
                order_id = self.tree.item(item)['values'][0]
                current_status = self.tree.item(item)['values'][4]  # Assuming 'Status' is the 5th column

                if current_status != 'Pending':
                    logger.warning(f"Order ID {order_id} is not 'Pending'. Current status: {current_status}")
                    messagebox.showwarning("Status Warning", f"Order ID {order_id} is not 'Pending'. Cannot mark as 'Ready for Delivery'.")
                    continue

                # Update order status to 'Ready for Delivery'
                self.cursor.execute("""
                    UPDATE customerorder 
                    SET status = 'Ready for Delivery' 
                    WHERE order_id = %s
                """, (order_id,))
                logger.info(f"Order ID {order_id} marked as 'Ready for Delivery'.")

            # Commit the changes after all updates
            self.connection.commit()
            messagebox.showinfo("Success", "Selected orders have been marked as 'Ready for Delivery'.")
            logger.info(f"Successfully marked {len(selected_items)} orders as 'Ready for Delivery'.")

        except Exception as e:
            # Rollback in case of any error during the update
            self.connection.rollback()
            logger.error(f"Failed to mark orders as ready for delivery: {e}")
            messagebox.showerror("Database Error", f"Failed to mark orders as ready for delivery: {e}")

        # Refresh the Treeview to reflect updated statuses
        self.populate_orders()


    def assign_delivery_personnel(self):
        """Assign delivery personnel to orders with grouping logic."""
        try:
            # Fetch all orders that are 'Ready for Delivery' and not yet assigned
            self.cursor.execute("""
                SELECT co.order_id, co.order_date, c.name AS customer_name, c.address, co.status
                FROM customerorder co
                JOIN customer c ON co.customer_id = c.customer_id
                LEFT JOIN deliveryassignment da ON co.order_id = da.order_id
                WHERE co.status = 'Ready for Delivery' AND da.order_id IS NULL
                ORDER BY co.order_date ASC
            """)
            orders = self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to fetch orders: {e}")
            messagebox.showerror("Database Error", f"Failed to fetch orders: {e}")
            return
        
        if not orders:
            messagebox.showinfo("Info", "No 'Ready for Delivery' orders available for assignment.")
            logger.info("No 'Ready for Delivery' orders available for assignment.")
            return

        # Group orders by postal code
        orders_by_postal_code = {}
        for order in orders:
            postal_code = self.extract_postal_code(order['address'])
            if postal_code not in orders_by_postal_code:
                orders_by_postal_code[postal_code] = []
            orders_by_postal_code[postal_code].append(order)
        
        logger.info(f"Grouped orders by postal code: {list(orders_by_postal_code.keys())}")
        
        for postal_code, orders_list in orders_by_postal_code.items():
            if postal_code == 'Unknown':
                logger.warning(f"Skipping orders with unknown postal code: {postal_code}")
                continue  # Skip orders with unknown postal codes

            # Batch orders within 3-minute window, max 3 pizzas
            batch = []
            for order in orders_list:
                if not batch:
                    batch.append(order)
                else:
                    time_diff = order['order_date'] - batch[0]['order_date']
                    if time_diff <= timedelta(minutes=3) and len(batch) < 3:
                        batch.append(order)
                    else:
                        break  # Start new batch
            
            if not batch:
                logger.info(f"No suitable batch found for postal code {postal_code}.")
                continue
            
            logger.info(f"Processing batch of {len(batch)} orders for postal code {postal_code}.")

            # Find available delivery personnel for the postal code
            self.cursor.execute("""
                SELECT dp.delivery_person_id, dp.name
                FROM deliverypersonnel dp
                WHERE dp.assigned_postal_code = %s AND dp.availability = 1
            """, (postal_code,))
            personnel = self.cursor.fetchall()
            
            if not personnel:
                logger.info(f"No available delivery personnel for postal code {postal_code}.")
                continue  # No available delivery person
            
            delivery_person_id = personnel[0]['delivery_person_id']
            delivery_person_name = personnel[0]['name']
            
            logger.info(f"Assigning delivery person '{delivery_person_name}' (ID: {delivery_person_id}) to postal code {postal_code}.")
            
            # Assign delivery person to all orders in batch
            try:
                for order in batch:
                    order_id = order['order_id']
                    self.cursor.execute("""
                        INSERT INTO deliveryassignment (order_id, delivery_person_id, assigned_at)
                        VALUES (%s, %s, %s)
                    """, (order_id, delivery_person_id, datetime.now()))
                    
                    # Update order status to 'Out for Delivery'
                    self.cursor.execute("""
                        UPDATE customerorder SET status = 'Out for Delivery' WHERE order_id = %s
                    """, (order_id,))
                    logger.info(f"Assigned Order ID {order_id} to '{delivery_person_name}'. Status updated to 'Out for Delivery'.")
                
                # Update delivery person availability to unavailable
                self.cursor.execute("""
                    UPDATE deliverypersonnel SET availability = 0 WHERE delivery_person_id = %s
                """, (delivery_person_id,))
                logger.info(f"Set delivery person '{delivery_person_name}' (ID: {delivery_person_id}) availability to 'Unavailable'.")
                
                self.connection.commit()
                
                messagebox.showinfo(
                    "Success",
                    f"Assigned {len(batch)} orders in postal code {postal_code} to {delivery_person_name}."
                )
                logger.info(f"Successfully assigned {len(batch)} orders to '{delivery_person_name}'.")
            except Exception as e:
                self.connection.rollback()
                logger.error(f"Failed to assign delivery personnel: {e}")
                messagebox.showerror("Database Error", f"Failed to assign delivery personnel: {e}")
        
    def manage_delivery_personnel(self):
        """Open a window to manage delivery personnel."""
        personnel_window = tk.Toplevel(self.parent)
        personnel_window.title("Manage Delivery Personnel")
        personnel_window.geometry("600x400")
        personnel_window.grab_set()
        
        # Controls Frame
        controls_frame = ttk.Frame(personnel_window)
        controls_frame.pack(fill='x', pady=10, padx=10)
        
        # Add Personnel Button
        add_button = ttk.Button(
            controls_frame,
            text="Add Personnel",
            bootstyle="success",
            command=lambda: self.add_personnel(personnel_window)
        )
        add_button.pack(side='left', padx=5)
        
        # Edit Personnel Button
        edit_button = ttk.Button(
            controls_frame,
            text="Edit Selected",
            bootstyle="primary",
            command=lambda: self.edit_personnel(personnel_window)
        )
        edit_button.pack(side='left', padx=5)
        
        # Delete Personnel Button
        delete_button = ttk.Button(
            controls_frame,
            text="Delete Selected",
            bootstyle="danger",
            command=lambda: self.delete_personnel(personnel_window)
        )
        delete_button.pack(side='left', padx=5)
        
        # Treeview to display personnel
        columns = ("ID", "Name", "Assigned Postal Code", "Availability")
        self.personnel_tree = ttk.Treeview(personnel_window, columns=columns, show='headings')
        for col in columns:
            self.personnel_tree.heading(col, text=col)
            self.personnel_tree.column(col, anchor='center', width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(personnel_window, orient="vertical", command=self.personnel_tree.yview)
        self.personnel_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        
        self.personnel_tree.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Populate personnel
        self.populate_personnel()
    
    def populate_personnel(self):
        """Fetch and display delivery personnel."""
        try:
            self.cursor.execute("SELECT * FROM deliverypersonnel")
            personnel = self.cursor.fetchall()
            
            # Clear existing entries
            for item in self.personnel_tree.get_children():
                self.personnel_tree.delete(item)
            
            for person in personnel:
                delivery_person_id = person['delivery_person_id']
                name = person['name']
                assigned_postal_code = person['assigned_postal_code']
                availability = 'Available' if person['availability'] else 'Unavailable'
                
                self.personnel_tree.insert("", tk.END, values=(
                    delivery_person_id,
                    name,
                    assigned_postal_code,
                    availability
                ))
        except Exception as e:
            logger.error(f"Failed to fetch personnel: {e}")
            messagebox.showerror("Database Error", f"Failed to fetch personnel: {e}")
    
    def add_personnel(self, window):
        """Add a new delivery person."""
        add_window = tk.Toplevel(window)
        add_window.title("Add Delivery Personnel")
        add_window.geometry("400x300")
        add_window.grab_set()
        
        ttk.Label(add_window, text="Name:").pack(pady=5)
        name_entry = ttk.Entry(add_window)
        name_entry.pack(pady=5)
        
        ttk.Label(add_window, text="Assigned Postal Code:").pack(pady=5)
        postal_code_entry = ttk.Entry(add_window)
        postal_code_entry.pack(pady=5)
        
        def save_personnel():
            name = name_entry.get().strip()
            assigned_postal_code = postal_code_entry.get().strip()
            
            if not name or not assigned_postal_code:
                messagebox.showerror("Input Error", "Please fill in all fields.")
                return
            
            # Validate postal code format (assuming 4-digit)
            if not re.match(r'^\d{4}$', assigned_postal_code):
                messagebox.showerror("Input Error", "Please enter a valid 4-digit postal code.")
                return
            
            try:
                self.cursor.execute("""
                    INSERT INTO deliverypersonnel (name, assigned_postal_code, availability)
                    VALUES (%s, %s, %s)
                """, (name, assigned_postal_code, 1))
                self.connection.commit()
                messagebox.showinfo("Success", f"Delivery personnel '{name}' added successfully.")
                add_window.destroy()
                self.populate_personnel()
            except Exception as e:
                self.connection.rollback()
                logger.error(f"Failed to add personnel: {e}")
                messagebox.showerror("Database Error", f"Failed to add personnel: {e}")
        
        ttk.Button(add_window, text="Save", bootstyle="success", command=save_personnel).pack(pady=20)
    
    def edit_personnel(self, window):
        """Edit selected delivery person."""
        selected = self.personnel_tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a delivery person to edit.")
            return
        
        item = self.personnel_tree.item(selected[0])['values']
        delivery_person_id, name, assigned_postal_code, availability = item
        
        edit_window = tk.Toplevel(window)
        edit_window.title("Edit Delivery Personnel")
        edit_window.geometry("400x300")
        edit_window.grab_set()
        
        ttk.Label(edit_window, text="Name:").pack(pady=5)
        name_entry = ttk.Entry(edit_window)
        name_entry.insert(0, name)
        name_entry.pack(pady=5)
        
        ttk.Label(edit_window, text="Assigned Postal Code:").pack(pady=5)
        postal_code_entry = ttk.Entry(edit_window)
        postal_code_entry.insert(0, assigned_postal_code)
        postal_code_entry.pack(pady=5)
        
        availability_var = tk.IntVar(value=1 if availability == 'Available' else 0)
        availability_checkbox = ttk.Checkbutton(edit_window, text="Available", variable=availability_var)
        availability_checkbox.pack(pady=5)
        
        def save_changes():
            name_new = name_entry.get().strip()
            postal_code_new = postal_code_entry.get().strip()
            availability_new = availability_var.get()
            
            if not name_new or not postal_code_new:
                messagebox.showerror("Input Error", "Please fill in all fields.")
                return
            
            # Validate postal code format (assuming 4-digit)
            if not re.match(r'^\d{4}$', postal_code_new):
                messagebox.showerror("Input Error", "Please enter a valid 4-digit postal code.")
                return
            
            try:
                self.cursor.execute("""
                    UPDATE deliverypersonnel
                    SET name = %s, assigned_postal_code = %s, availability = %s
                    WHERE delivery_person_id = %s
                """, (name_new, postal_code_new, availability_new, delivery_person_id))
                self.connection.commit()
                messagebox.showinfo("Success", f"Delivery personnel '{name_new}' updated successfully.")
                edit_window.destroy()
                self.populate_personnel()
            except Exception as e:
                self.connection.rollback()
                logger.error(f"Failed to update personnel: {e}")
                messagebox.showerror("Database Error", f"Failed to update personnel: {e}")
        
        ttk.Button(edit_window, text="Save Changes", bootstyle="primary", command=save_changes).pack(pady=20)
    
    def delete_personnel(self, window):
        """Delete selected delivery person."""
        selected = self.personnel_tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a delivery person to delete.")
            return
        
        item = self.personnel_tree.item(selected[0])['values']
        delivery_person_id = item[0]
        name = item[1]
        
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete delivery person '{name}'?"
        )
        if not confirm:
            return
        
        try:
            # Check if the delivery person has any active assignments
            self.cursor.execute("""
                SELECT * FROM deliveryassignment WHERE delivery_person_id = %s
            """, (delivery_person_id,))
            assignments = self.cursor.fetchall()
            if assignments:
                messagebox.showerror("Deletion Error", f"Cannot delete delivery person '{name}' as they have active assignments.")
                return
            
            self.cursor.execute("""
                DELETE FROM deliverypersonnel WHERE delivery_person_id = %s
            """, (delivery_person_id,))
            self.connection.commit()
            messagebox.showinfo("Success", f"Delivery person '{name}' deleted successfully.")
            self.populate_personnel()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to delete personnel: {e}")
            messagebox.showerror("Database Error", f"Failed to delete personnel: {e}")
    
    def mark_as_delivered(self):
        """Mark selected orders as delivered."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Selection Error", "Please select at least one order to mark as delivered.")
            return

        try:
            for item in selected_items:
                order_id = self.tree.item(item)['values'][0]
                status = self.tree.item(item)['values'][4]  # Status column

                if status not in ['Ready for Delivery', 'Out for Delivery']:
                    logger.warning(f"Order ID {order_id} is neither 'Ready for Delivery' nor 'Out for Delivery'. Current status: {status}")
                    messagebox.showwarning("Status Warning", f"Order ID {order_id} is neither 'Ready for Delivery' nor 'Out for Delivery'.")
                    continue

                # Update order status to 'Delivered'
                self.cursor.execute("""
                    UPDATE customerorder SET status = 'Delivered' WHERE order_id = %s
                """, (order_id,))

                # Update delivery person availability
                self.cursor.execute("""
                    SELECT delivery_person_id FROM deliveryassignment WHERE order_id = %s
                """, (order_id,))
                delivery_assignment = self.cursor.fetchone()
                if delivery_assignment:
                    delivery_person_id = delivery_assignment['delivery_person_id']
                    self.cursor.execute("""
                        UPDATE deliverypersonnel SET availability = 1 WHERE delivery_person_id = %s
                    """, (delivery_person_id,))
                    logger.info(f"Set delivery person ID {delivery_person_id} availability to 'Available'.")

            self.connection.commit()
            messagebox.showinfo("Success", "Selected orders have been marked as delivered.")
            logger.info(f"Marked {len(selected_items)} orders as delivered.")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to mark orders as delivered: {e}")
            messagebox.showerror("Database Error", f"Failed to mark orders as delivered: {e}")

        # Refresh the order list
        self.populate_orders()

    def update_delivery_personnel_availability(self):
        """Update delivery personnel availability after 30 minutes."""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=30)
            self.cursor.execute("""
                SELECT da.delivery_person_id
                FROM deliveryassignment da
                JOIN customerorder co ON da.order_id = co.order_id
                WHERE da.assigned_at <= %s
                AND co.status = 'Out for Delivery'
            """, (cutoff_time,))
            personnel_to_update = self.cursor.fetchall()

            for person in personnel_to_update:
                delivery_person_id = person['delivery_person_id']
                # Update availability
                self.cursor.execute("""
                    UPDATE deliverypersonnel SET availability = 1 WHERE delivery_person_id = %s
                """, (delivery_person_id,))
                logger.info(f"Updated availability for delivery person ID {delivery_person_id}.")
            
            self.connection.commit()
        except Exception as e:
            logger.error(f"Failed to update availability: {e}")
            self.connection.rollback()
    
    def schedule_availability_update(self):
        """Schedule periodic availability updates."""
        self.update_delivery_personnel_availability()
        # Schedule next update after 5 minutes (300,000 milliseconds)
        self.parent.after(300000, self.schedule_availability_update)
    
    def refresh(self):
        """Refresh the delivery management data."""
        self.populate_orders()

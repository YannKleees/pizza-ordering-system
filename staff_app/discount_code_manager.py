import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import ttk
import logging
from datetime import datetime
from ttkbootstrap.widgets import DateEntry  # Corrected import

logger = logging.getLogger(__name__)

class DiscountCodeManager:
    def __init__(self, parent, cursor, connection):
        self.parent = parent
        self.cursor = cursor
        self.connection = connection
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the Discount Code Manager UI components."""
        self.parent.pack(fill='both', expand=True)
        
        # Controls Frame
        controls_frame = ttk.Frame(self.parent)
        controls_frame.pack(fill='x', pady=10, padx=10)
        
        # Add Discount Code Button
        add_button = ttk.Button(
            controls_frame,
            text="Add Discount Code",
            bootstyle="success",
            command=self.add_discount_code
        )
        add_button.pack(side='left', padx=5)
        
        # Edit Discount Code Button
        edit_button = ttk.Button(
            controls_frame,
            text="Edit Selected Code",
            bootstyle="primary",
            command=self.edit_discount_code
        )
        edit_button.pack(side='left', padx=5)
        
        # Delete Discount Code Button
        delete_button = ttk.Button(
            controls_frame,
            text="Delete Selected Code",
            bootstyle="danger",
            command=self.delete_discount_code
        )
        delete_button.pack(side='left', padx=5)
        
        # Refresh Button
        refresh_button = ttk.Button(
            controls_frame,
            text="Refresh",
            bootstyle="info",
            command=self.populate_discount_codes
        )
        refresh_button.pack(side='left', padx=5)
        
        # Treeview to display discount codes
        columns = ("Code", "Expiration Date", "Discount (%)", "Is Used")
        self.tree = ttk.Treeview(self.parent, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        
        self.tree.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Populate discount codes
        self.populate_discount_codes()
    
    def populate_discount_codes(self):
        """Fetch and display discount codes."""
        try:
            self.cursor.execute("SELECT * FROM discountcode")
            discount_codes = self.cursor.fetchall()
            
            # Clear existing entries
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            for code in discount_codes:
                code_str = code['code']
                expiration_date = code['expiration_date'].strftime('%Y-%m-%d')
                discount_percentage = f"{code['discount_percentage']:.2f}"
                is_used = 'Yes' if code['is_used'] else 'No'
                
                self.tree.insert("", tk.END, values=(
                    code_str,
                    expiration_date,
                    discount_percentage,
                    is_used
                ))
        except Exception as e:
            logger.error(f"Failed to fetch discount codes: {e}")
            messagebox.showerror("Database Error", f"Failed to fetch discount codes: {e}")
    
    def add_discount_code(self):
        """Open a dialog to add a new discount code."""
        add_window = tk.Toplevel(self.parent)
        add_window.title("Add Discount Code")
        add_window.geometry("400x300")
        add_window.grab_set()
        
        ttk.Label(add_window, text="Code:").pack(pady=5)
        code_entry = ttk.Entry(add_window)
        code_entry.pack(pady=5)
        
        ttk.Label(add_window, text="Expiration Date:").pack(pady=5)
        expiration_date_entry = DateEntry(add_window, dateformat='%Y-%m-%d')
        expiration_date_entry.pack(pady=5)
        
        ttk.Label(add_window, text="Discount Percentage:").pack(pady=5)
        discount_percentage_entry = ttk.Entry(add_window)
        discount_percentage_entry.pack(pady=5)
        
        def save_discount_code():
            code = code_entry.get().strip()
            expiration_date = expiration_date_entry.entry.get()
            discount_percentage_str = discount_percentage_entry.get().strip()
            
            if not code or not discount_percentage_str or not expiration_date:
                messagebox.showerror("Input Error", "Please fill in all fields.")
                return
            
            try:
                discount_percentage = float(discount_percentage_str)
                if discount_percentage < 0 or discount_percentage > 100:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Input Error",
                    "Please enter a valid discount percentage between 0 and 100."
                )
                return
            
            try:
                # Insert into discountcode table
                self.cursor.execute(
                    "INSERT INTO discountcode (code, expiration_date, discount_percentage, is_used) VALUES (%s, %s, %s, %s)",
                    (code, expiration_date, discount_percentage, 0)
                )
                self.connection.commit()
                messagebox.showinfo("Success", f"Discount code '{code}' added successfully.")
                add_window.destroy()
                self.populate_discount_codes()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to add discount code: {e}")
                self.connection.rollback()
        
        ttk.Button(add_window, text="Save", bootstyle="success", command=save_discount_code).pack(pady=20)
    
    def edit_discount_code(self):
        """Edit the selected discount code."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a discount code to edit.")
            return
        
        item = self.tree.item(selected[0])['values']
        code_str, expiration_date_str, discount_percentage_str, is_used_str = item
        
        edit_window = tk.Toplevel(self.parent)
        edit_window.title("Edit Discount Code")
        edit_window.geometry("400x300")
        edit_window.grab_set()
        
        ttk.Label(edit_window, text="Code:").pack(pady=5)
        code_entry = ttk.Entry(edit_window)
        code_entry.insert(0, code_str)
        code_entry.config(state='disabled')  # Code is primary key, should not change
        code_entry.pack(pady=5)
        
        ttk.Label(edit_window, text="Expiration Date:").pack(pady=5)
        expiration_date_entry = DateEntry(edit_window, dateformat='%Y-%m-%d')
        expiration_date_entry.entry.delete(0, tk.END)
        expiration_date_entry.entry.insert(0, expiration_date_str)
        expiration_date_entry.pack(pady=5)
        
        ttk.Label(edit_window, text="Discount Percentage:").pack(pady=5)
        discount_percentage_entry = ttk.Entry(edit_window)
        discount_percentage_entry.insert(0, discount_percentage_str)
        discount_percentage_entry.pack(pady=5)
        
        is_used_var = tk.IntVar(value=1 if is_used_str == 'Yes' else 0)
        is_used_checkbox = ttk.Checkbutton(edit_window, text="Is Used", variable=is_used_var)
        is_used_checkbox.pack(pady=5)
        
        def save_changes():
            expiration_date = expiration_date_entry.entry.get()
            discount_percentage_str_new = discount_percentage_entry.get().strip()
            is_used_new = is_used_var.get()
            
            if not discount_percentage_str_new or not expiration_date:
                messagebox.showerror("Input Error", "Please fill in all fields.")
                return
            
            try:
                discount_percentage_new = float(discount_percentage_str_new)
                if discount_percentage_new < 0 or discount_percentage_new > 100:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Input Error",
                    "Please enter a valid discount percentage between 0 and 100."
                )
                return
            
            try:
                # Update discountcode table
                self.cursor.execute(
                    "UPDATE discountcode SET expiration_date = %s, discount_percentage = %s, is_used = %s WHERE code = %s",
                    (expiration_date, discount_percentage_new, is_used_new, code_str)
                )
                self.connection.commit()
                messagebox.showinfo("Success", f"Discount code '{code_str}' updated successfully.")
                edit_window.destroy()
                self.populate_discount_codes()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to update discount code: {e}")
                self.connection.rollback()
        
        ttk.Button(edit_window, text="Save Changes", bootstyle="primary", command=save_changes).pack(pady=20)
    
    def delete_discount_code(self):
        """Delete the selected discount code."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a discount code to delete.")
            return
        
        item = self.tree.item(selected[0])['values']
        code_str = item[0]
        
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete discount code '{code_str}'?"
        )
        if not confirm:
            return
        
        try:
            self.cursor.execute("DELETE FROM discountcode WHERE code = %s", (code_str,))
            self.connection.commit()
            messagebox.showinfo("Success", f"Discount code '{code_str}' deleted successfully.")
            self.populate_discount_codes()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to delete discount code: {e}")
            self.connection.rollback()
    
    def refresh(self):
        """Refresh the discount codes."""
        self.populate_discount_codes()

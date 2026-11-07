import tkinter as tk
from tkinter import messagebox, simpledialog  # Import simpledialog for input
from ttkbootstrap import ttk
from ttkbootstrap.constants import *
import logging
from decimal import Decimal, ROUND_HALF_UP  # Import Decimal and rounding

# Configure logging to a file for persistent logs
logging.basicConfig(
    filename='staff_app.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s'
)

logger = logging.getLogger(__name__)

class MenuManagement:
    def __init__(self, parent, cursor, connection):
        self.parent = parent
        self.cursor = cursor
        self.connection = connection
        self.setup_ui()

    def setup_ui(self):
        """Initialize the Menu Management UI components."""
        logger.info("Setting up Menu Management UI.")
        # Clear any existing content in the parent frame
        for widget in self.parent.winfo_children():
            widget.destroy()

        self.parent.pack(fill='both', expand=True)

        # Create a frame for controls
        controls_frame = ttk.Frame(self.parent)
        controls_frame.pack(fill='x', pady=10, padx=10)

        # Add Menu Item Button
        add_button = ttk.Button(controls_frame, text="Add Menu Item", bootstyle="success",
                                command=self.add_menu_item)
        add_button.pack(side='left', padx=5)

        # Edit Menu Item Button
        edit_button = ttk.Button(controls_frame, text="Edit Selected Item", bootstyle="primary",
                                 command=self.edit_menu_item)
        edit_button.pack(side='left', padx=5)

        # Delete Menu Item Button
        delete_button = ttk.Button(controls_frame, text="Delete Selected Item", bootstyle="danger",
                                   command=self.delete_menu_item)
        delete_button.pack(side='left', padx=5)

        # Refresh Button
        refresh_button = ttk.Button(controls_frame, text="Refresh", bootstyle="info",
                                    command=self.populate_menu_items)
        refresh_button.pack(side='left', padx=5)

        # Create a Treeview to display menu items
        columns = ("Category", "Item ID", "Name", "Price (€)")
        self.tree = ttk.Treeview(self.parent, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Name":
                self.tree.column(col, width=200, anchor='center')
            else:
                self.tree.column(col, anchor='center')

        # Add scrollbar to the Treeview
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        # Populate menu items
        self.populate_menu_items()
        logger.info("Menu Management UI setup completed.")

    def fetch_menu_items(self):
        """Fetch all menu items."""
        try:
            self.cursor.execute("""
                SELECT type AS category, menu_item_id AS item_id, name, price
                FROM menu_item
                ORDER BY category, name
            """)
            items = self.cursor.fetchall()
            logger.info(f"Fetched {len(items)} menu items.")
            return items
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch menu items: {e}")
            logger.error(f"Error fetching menu items: {e}")
            return []

    def populate_menu_items(self):
        """Populate the Menu Management tab with menu items."""
        logger.info("Populating menu items in the Treeview.")
        # Clear existing entries
        for item in self.tree.get_children():
            self.tree.delete(item)

        menu_items = self.fetch_menu_items()

        if not menu_items:
            ttk.Label(self.parent, text="No menu items available.", font=("Helvetica", 12)).pack(pady=10)
            logger.info("No menu items to display.")
            return

        for item in menu_items:
            self.tree.insert("", tk.END, values=(
                item['category'],
                item['item_id'],
                item['name'],
                f"{item['price']:.2f}"
            ))
        logger.info("Menu items populated successfully.")

    def fetch_ingredients(self):
        """Fetch all available ingredients."""
        try:
            self.cursor.execute("SELECT ingredient_id, name FROM ingredient ORDER BY name")
            ingredients = self.cursor.fetchall()
            logger.info(f"Fetched {len(ingredients)} ingredients.")
            return ingredients
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch ingredients: {e}")
            logger.error(f"Failed to fetch ingredients: {e}")
            return []

    def fetch_pizza_ingredients(self, pizza_id):
        """Fetch ingredients associated with a specific pizza."""
        try:
            self.cursor.execute("""
                SELECT i.ingredient_id, i.name
                FROM ingredient i
                JOIN pizza_ingredient pi ON i.ingredient_id = pi.ingredient_id
                WHERE pi.pizza_id = %s
                ORDER BY i.name
            """, (pizza_id,))
            ingredients = self.cursor.fetchall()
            logger.info(f"Fetched {len(ingredients)} ingredients for pizza ID {pizza_id}.")
            return ingredients
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch pizza ingredients: {e}")
            logger.error(f"Failed to fetch pizza ingredients: {e}")
            return []

    def add_menu_item(self):
        """Open a dialog to add a new menu item."""
        logger.info("Opening 'Add Menu Item' dialog.")
        add_window = tk.Toplevel(self.parent)
        add_window.title("Add Menu Item")
        add_window.geometry("600x1000")
        add_window.grab_set()  # Make the window modal

        try:
            ttk.Label(add_window, text="Category:").pack(pady=5)
            category_combobox = ttk.Combobox(add_window, values=["Pizza", "Drink", "Dessert"], state="readonly")
            category_combobox.pack(pady=5)
            category_combobox.current(0)

            ttk.Label(add_window, text="Name:").pack(pady=5)
            name_entry = ttk.Entry(add_window)
            name_entry.pack(pady=5)

            # Price field is **disabled** to prevent manual editing
            ttk.Label(add_window, text="Price (€):").pack(pady=5)
            price_entry = ttk.Entry(add_window, state='disabled')
            price_entry.pack(pady=5)
            price_entry.insert(0, "Calculated Automatically")

            # Ingredients Section (Only for Pizza)
            ingredients_frame = ttk.Frame(add_window)
            ingredients_frame.pack(pady=10, fill='both', expand=True)

            ingredients_label = ttk.Label(ingredients_frame, text="Select Ingredients:")
            ingredients_label.pack(pady=5)

            ingredients_listbox = tk.Listbox(ingredients_frame, selectmode='multiple')
            ingredients_listbox.pack(fill='both', expand=True, padx=10, pady=5)

            # Fetch ingredients and populate the listbox
            all_ingredients = self.fetch_ingredients()
            for ingredient in all_ingredients:
                ingredients_listbox.insert(tk.END, ingredient['name'])

            def on_category_change(event):
                category = category_combobox.get()
                if category == "Pizza":
                    ingredients_frame.pack(pady=10, fill='both', expand=True)
                else:
                    ingredients_frame.pack_forget()

            category_combobox.bind("<<ComboboxSelected>>", on_category_change)

        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to set up 'Add Menu Item' dialog: {e}")
            logger.error(f"Failed to set up 'Add Menu Item' dialog: {e}")
            add_window.destroy()
            return

    def save_menu_item():
        logger.info("Attempting to save new menu item.")
        category = category_combobox.get()
        name = name_entry.get().strip()

        if not name:
            messagebox.showerror("Input Error", "Please enter the name of the menu item.")
            logger.warning("Save failed: Name field is empty.")
            return

        try:
            # Calculate price automatically based on ingredients if Pizza
            if category == "Pizza":
                selected_indices = ingredients_listbox.curselection()
                selected_ingredient_ids = [all_ingredients[i]['ingredient_id'] for i in selected_indices]

                if not selected_ingredient_ids:
                    messagebox.showerror("Input Error", "Please select at least one ingredient for Pizza.")
                    logger.warning("Save failed: No ingredients selected for Pizza.")
                    return

                # Calculate total ingredient cost
                format_strings = ','.join(['%s'] * len(selected_ingredient_ids))
                self.cursor.execute(f"""
                    SELECT SUM(cost) AS total_cost
                    FROM ingredient
                    WHERE ingredient_id IN ({format_strings})
                """, tuple(selected_ingredient_ids))
                result = self.cursor.fetchone()
                total_cost = Decimal(str(result['total_cost'])) if result['total_cost'] else Decimal('0.00')

                # Define profit margin and VAT as Decimal
                profit_margin = Decimal('0.40')  # 40%
                vat = Decimal('0.09')             # 9%
                base_price = Decimal('0.00')      # Assuming base price is 0.00

                # Calculate final price using Decimal arithmetic
                final_price = (total_cost + base_price) * (Decimal('1.00') + profit_margin) * (Decimal('1.00') + vat)
                final_price = final_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                if final_price <= Decimal('0.00'):
                    raise ValueError("Calculated price must be greater than zero.")

            else:
                # For Drink and Dessert, prompt for price
                price_input = simpledialog.askfloat("Input", "Enter the price (€):", minvalue=0.0)
                if price_input is None:
                    logger.info("Save cancelled by user.")
                    return  # User cancelled

                # Ensure that price_input is a valid float
                if not isinstance(price_input, (float, int)):
                    raise ValueError("Invalid price input.")

                final_price = Decimal(str(round(price_input, 2))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                if final_price <= Decimal('0.00'):
                    raise ValueError("Price must be greater than zero.")

        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failed to calculate price: {e}")
            logger.error(f"Price calculation failed: {e}")
            return

        try:
            # Insert into menu_item table with final_price as float
            self.cursor.execute(
                "INSERT INTO menu_item (name, type, price) VALUES (%s, %s, %s)",
                (name, category, float(final_price))  # Convert Decimal to float
            )
            menu_item_id = self.cursor.lastrowid
            logger.info(f"Inserted menu_item '{name}' with ID {menu_item_id}.")

            if category == "Pizza":
                # Insert into pizza table with appropriate conversions
                self.cursor.execute(
                    "INSERT INTO pizza (pizza_id, name, size, price, is_vegetarian, is_vegan, profit_margin, vat, base_price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        menu_item_id,
                        name,
                        'Medium',
                        float(final_price),      # Convert Decimal to float
                        0,                        # is_vegetarian
                        0,                        # is_vegan
                        float(profit_margin),     # Convert Decimal to float
                        float(vat),               # Convert Decimal to float
                        float(base_price)         # Convert Decimal to float
                    )
                )
                logger.info(f"Inserted pizza '{name}' with ID {menu_item_id}.")

                # Insert into pizza_ingredient table
                for ingredient_id in selected_ingredient_ids:
                    self.cursor.execute(
                        "INSERT INTO pizza_ingredient (pizza_id, ingredient_id) VALUES (%s, %s)",
                        (menu_item_id, ingredient_id)
                    )
                    logger.info(f"Linked ingredient ID {ingredient_id} to pizza ID {menu_item_id}.")

            self.connection.commit()
            logger.info(f"Menu item '{name}' added successfully.")
            messagebox.showinfo("Success", f"{category} '{name}' added successfully with price €{final_price:.2f}.")
            add_window.destroy()
            self.populate_menu_items()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add menu item: {e}")
            logger.error(f"Error adding menu item: {e}")
            self.connection.rollback()



    def edit_menu_item(self):
        """Edit the selected menu item."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a menu item to edit.")
            return

        item = self.tree.item(selected[0])['values']
        category, item_id, name, price = item

        logger.info(f"Opening 'Edit Menu Item' dialog for {category} '{name}'.")

        edit_window = tk.Toplevel(self.parent)
        edit_window.title("Edit Menu Item")
        edit_window.geometry("400x700")
        edit_window.grab_set()  # Make the window modal

        try:
            ttk.Label(edit_window, text="Category:").pack(pady=5)
            category_label = ttk.Label(edit_window, text=category)
            category_label.pack(pady=5)

            ttk.Label(edit_window, text="Name:").pack(pady=5)
            name_entry = ttk.Entry(edit_window)
            name_entry.insert(0, name)
            name_entry.pack(pady=5)
            # Price field is **disabled** to prevent manual editing
            ttk.Label(edit_window, text="Price (€):").pack(pady=5)
            price_entry = ttk.Entry(edit_window, state='disabled')
            price_entry.pack(pady=5)
            price_entry.insert(0, "Calculated Automatically")

            # Ingredients Section (Only for Pizza)
            ingredients_frame = ttk.Frame(edit_window)
            ingredients_frame.pack(pady=10, fill='both', expand=True)

            ingredients_label = ttk.Label(ingredients_frame, text="Select Ingredients:")
            ingredients_label.pack(pady=5)

            ingredients_listbox = tk.Listbox(ingredients_frame, selectmode='multiple')
            ingredients_listbox.pack(fill='both', expand=True, padx=10, pady=5)

            if category == "Pizza":
                # Fetch all ingredients
                all_ingredients = self.fetch_ingredients()
                for ingredient in all_ingredients:
                    ingredients_listbox.insert(tk.END, ingredient['name'])

                # Fetch selected pizza's ingredients
                pizza_ingredients = self.fetch_pizza_ingredients(item_id)
                pizza_ingredient_ids = [ingredient['ingredient_id'] for ingredient in pizza_ingredients]

                # Set selected ingredients in the listbox
                for index, ingredient in enumerate(all_ingredients):
                    if ingredient['ingredient_id'] in pizza_ingredient_ids:
                        ingredients_listbox.selection_set(index)
            else:
                ingredients_frame.pack_forget()

        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to set up 'Edit Menu Item' dialog: {e}")
            logger.error(f"Failed to set up 'Edit Menu Item' dialog: {e}")
            edit_window.destroy()
            return

        def save_changes():
            logger.info("Attempting to save changes to menu item.")
            new_name = name_entry.get().strip()

            if not new_name:
                messagebox.showerror("Input Error", "Please enter the name of the menu item.")
                logger.warning("Save failed: Name field is empty.")
                return

            try:
                # Calculate price automatically based on ingredients if Pizza
                if category == "Pizza":
                    selected_indices = ingredients_listbox.curselection()
                    selected_ingredient_ids = [all_ingredients[i]['ingredient_id'] for i in selected_indices]

                    if not selected_ingredient_ids:
                        messagebox.showerror("Input Error", "Please select at least one ingredient for Pizza.")
                        logger.warning("Save failed: No ingredients selected for Pizza.")
                        return

                    # Calculate total ingredient cost
                    format_strings = ','.join(['%s'] * len(selected_ingredient_ids))
                    self.cursor.execute(f"""
                        SELECT SUM(cost) AS total_cost
                        FROM ingredient
                        WHERE ingredient_id IN ({format_strings})
                    """, tuple(selected_ingredient_ids))
                    result = self.cursor.fetchone()
                    total_cost = Decimal(str(result['total_cost'])) if result['total_cost'] else Decimal('0.00')

                    # Define profit margin and VAT as Decimal
                    profit_margin = Decimal('0.40')  # 40%
                    vat = Decimal('0.09')             # 9%
                    base_price = Decimal('0.00')      # Assuming base price is 0.00

                    # Calculate final price using Decimal arithmetic
                    final_price = (total_cost + base_price) * (Decimal('1.00') + profit_margin) * (Decimal('1.00') + vat)
                    final_price = final_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                    if final_price <= Decimal('0.00'):
                        raise ValueError("Calculated price must be greater than zero.")

                else:
                    # For Drink and Dessert, prompt for price
                    price_input = simpledialog.askfloat("Input", "Enter the price (€):", minvalue=0.0)
                    if price_input is None:
                        logger.info("Save Changes cancelled by user.")
                        return  # User cancelled

                    # Ensure that price_input is a valid float
                    if not isinstance(price_input, (float, int)):
                        raise ValueError("Invalid price input.")

                    final_price = Decimal(str(round(price_input, 2))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                    if final_price <= Decimal('0.00'):
                        raise ValueError("Price must be greater than zero.")

            except Exception as e:
                messagebox.showerror("Calculation Error", f"Failed to calculate price: {e}")
                logger.error(f"Price calculation failed: {e}")
                return

            try:
                # Update menu_item table with final_price as float
                self.cursor.execute(
                    "UPDATE menu_item SET name = %s, price = %s WHERE menu_item_id = %s",
                    (new_name, float(final_price), item_id)  # Convert Decimal to float
                )
                logger.info(f"Updated menu_item '{new_name}' with ID {item_id}.")

                if category == "Pizza":
                    # Update pizza table with final_price as float
                    self.cursor.execute(
                        "UPDATE pizza SET name = %s, price = %s WHERE pizza_id = %s",
                        (new_name, float(final_price), item_id)  # Convert Decimal to float
                    )
                    logger.info(f"Updated pizza '{new_name}' with ID {item_id}.")

                    # Update ingredients
                    selected_indices = ingredients_listbox.curselection()
                    selected_ingredient_ids = [all_ingredients[i]['ingredient_id'] for i in selected_indices]

                    # Delete existing ingredients
                    self.cursor.execute("DELETE FROM pizza_ingredient WHERE pizza_id = %s", (item_id,))
                    logger.info(f"Deleted existing ingredients for pizza ID {item_id}.")

                    # Insert new ingredients
                    for ingredient_id in selected_ingredient_ids:
                        self.cursor.execute(
                            "INSERT INTO pizza_ingredient (pizza_id, ingredient_id) VALUES (%s, %s)",
                            (item_id, ingredient_id)
                        )
                        logger.info(f"Linked ingredient ID {ingredient_id} to pizza ID {item_id}.")
                self.connection.commit()
                logger.info(f"Menu item '{new_name}' updated successfully.")
                messagebox.showinfo("Success", f"{category} '{new_name}' updated successfully with price €{final_price:.2f}.")
                edit_window.destroy()
                self.populate_menu_items()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to update menu item: {e}")
                logger.error(f"Error updating menu item: {e}")
                self.connection.rollback()

        try:
            ttk.Button(edit_window, text="Save Changes", bootstyle="primary", command=save_changes).pack(pady=20)
            logger.info("'Save Changes' button packed successfully in 'Edit Menu Item' dialog.")
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to create 'Save Changes' button: {e}")
            logger.error(f"Failed to create 'Save Changes' button: {e}")

    def delete_menu_item(self):
        """Delete the selected menu item."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a menu item to delete.")
            return

        item = self.tree.item(selected[0])['values']
        category, item_id, name, price = item

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {category} '{name}'?")
        if not confirm:
            return

        try:
            if category == "Pizza":
                # Delete from pizza_ingredient due to foreign key constraint
                self.cursor.execute("DELETE FROM pizza_ingredient WHERE pizza_id = %s", (item_id,))
                logger.info(f"Deleted pizza_ingredient records for pizza ID {item_id}.")

                # Delete from pizza
                self.cursor.execute("DELETE FROM pizza WHERE pizza_id = %s", (item_id,))
                logger.info(f"Deleted pizza record with ID {item_id}.")

            # Delete from menu_item
            self.cursor.execute("DELETE FROM menu_item WHERE menu_item_id = %s", (item_id,))
            logger.info(f"Deleted menu_item record with ID {item_id}.")

            self.connection.commit()
            messagebox.showinfo("Success", f"{category} '{name}' deleted successfully.")
            logger.info(f"Menu item '{name}' deleted successfully.")
            self.populate_menu_items()

            # After deleting menu item, if it's Pizza, recalculate pizza prices
            if category == "Pizza":
                self.recalculate_pizza_prices()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to delete menu item: {e}")
            logger.error(f"Error deleting menu item: {e}")
            self.connection.rollback()

    def refresh(self):
        """Refresh the menu items."""
        self.populate_menu_items()

    def recalculate_pizza_prices(self):
        """Recalculate pizza prices based on ingredient costs, profit margin, and VAT."""
        try:
            # Fetch all pizzas
            self.cursor.execute("SELECT pizza_id, profit_margin, vat, base_price FROM pizza")
            pizzas = self.cursor.fetchall()
            logger.info(f"Fetched {len(pizzas)} pizzas for recalculation.")

            for pizza in pizzas:
                pizza_id = pizza['pizza_id']
                
                # Convert fetched values to Decimal for precise calculations
                profit_margin = Decimal(str(pizza['profit_margin']))
                vat = Decimal(str(pizza['vat']))
                base_price = Decimal(str(pizza['base_price']))

                # Calculate total ingredient cost
                self.cursor.execute("""
                    SELECT SUM(i.cost) AS total_cost
                    FROM pizza_ingredient pi
                    JOIN ingredient i ON pi.ingredient_id = i.ingredient_id
                    WHERE pi.pizza_id = %s
                """, (pizza_id,))
                result = self.cursor.fetchone()
                total_cost = Decimal(str(result['total_cost'])) if result['total_cost'] else Decimal('0.00')

                # Calculate final price using Decimal arithmetic
                final_price = (total_cost + base_price) * (Decimal('1.00') + profit_margin) * (Decimal('1.00') + vat)
                final_price = final_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                if final_price <= Decimal('0.00'):
                    raise ValueError(f"Calculated price for pizza ID {pizza_id} must be greater than zero.")

                # Update pizza price in the pizza table
                self.cursor.execute(
                    "UPDATE pizza SET price = %s WHERE pizza_id = %s",
                    (float(final_price), pizza_id)  # Convert Decimal to float for database compatibility
                )
                logger.info(f"Updated pizza ID {pizza_id} price to €{final_price}.")

                # Update corresponding menu_item price
                self.cursor.execute(
                    "UPDATE menu_item SET price = %s WHERE menu_item_id = %s AND type = 'Pizza'",
                    (float(final_price), pizza_id)  # Convert Decimal to float for database compatibility
                )
                logger.info(f"Updated menu_item ID {pizza_id} price to €{final_price}.")

            self.connection.commit()
            logger.info("Recalculated and updated pizza prices based on ingredient costs.")
            messagebox.showinfo("Success", "Pizza prices have been recalculated based on updated ingredient costs.")

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to recalculate pizza prices: {e}")
            logger.error(f"Error recalculating pizza prices: {e}")
            self.connection.rollback()

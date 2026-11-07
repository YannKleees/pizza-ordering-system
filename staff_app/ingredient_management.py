import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import ttk
import logging

# Configure logging
logging.basicConfig(
    filename='ingredient_management.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)
logger = logging.getLogger(__name__)

class IngredientManagement:
    def __init__(self, parent, cursor, connection):
        self.parent = parent
        self.cursor = cursor
        self.connection = connection
        self.setup_ui()

    def setup_ui(self):
        """Initialize the Ingredient Management UI components."""
        # Clear any existing content in the parent frame
        for widget in self.parent.winfo_children():
            widget.destroy()

        self.parent.pack(fill='both', expand=True)

        # Create a frame for controls
        controls_frame = ttk.Frame(self.parent)
        controls_frame.pack(fill='x', pady=10, padx=10)

        # Add Ingredient Button
        add_button = ttk.Button(controls_frame, text="Add Ingredient", bootstyle="success",
                                command=self.add_ingredient)
        add_button.pack(side='left', padx=5)

        # Edit Ingredient Button
        edit_button = ttk.Button(controls_frame, text="Edit Selected Ingredient", bootstyle="primary",
                                 command=self.edit_ingredient)
        edit_button.pack(side='left', padx=5)

        # Delete Ingredient Button
        delete_button = ttk.Button(controls_frame, text="Delete Selected Ingredient", bootstyle="danger",
                                   command=self.delete_ingredient)
        delete_button.pack(side='left', padx=5)

        # Refresh Button
        refresh_button = ttk.Button(controls_frame, text="Refresh", bootstyle="info",
                                    command=self.populate_ingredients)
        refresh_button.pack(side='left', padx=5)

        # Create a Treeview to display ingredients
        columns = ("Ingredient ID", "Name", "Cost (€)", "Vegetarian", "Vegan")
        self.tree = ttk.Treeview(self.parent, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Name":
                self.tree.column(col, width=200, anchor='center')
            elif col == "Ingredient ID":
                self.tree.column(col, width=100, anchor='center')
            else:
                self.tree.column(col, anchor='center')

        # Add scrollbar to the Treeview
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        # Populate ingredients
        self.populate_ingredients()

    def fetch_ingredients(self):
        """Fetch all ingredients."""
        try:
            self.cursor.execute("""
                SELECT ingredient_id, name, cost, is_vegetarian, is_vegan
                FROM ingredient
                ORDER BY name
            """)
            ingredients = self.cursor.fetchall()
            return ingredients
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch ingredients: {e}")
            logger.error(f"Error fetching ingredients: {e}")
            return []

    def populate_ingredients(self):
        """Populate the Ingredient Management tab with ingredients."""
        # Clear existing entries
        for item in self.tree.get_children():
            self.tree.delete(item)

        ingredients = self.fetch_ingredients()

        if not ingredients:
            ttk.Label(self.parent, text="No ingredients available.", font=("Helvetica", 12)).pack(pady=10)
            return

        for ingredient in ingredients:
            vegetarian = "Yes" if ingredient['is_vegetarian'] else "No"
            vegan = "Yes" if ingredient['is_vegan'] else "No"
            self.tree.insert("", tk.END, values=(
                ingredient['ingredient_id'],
                ingredient['name'],
                f"{ingredient['cost']:.2f}",
                vegetarian,
                vegan
            ))

    def add_ingredient(self):
        """Open a dialog to add a new ingredient."""
        add_window = tk.Toplevel(self.parent)
        add_window.title("Add Ingredient")
        add_window.geometry("400x400")
        add_window.grab_set()  # Make the window modal

        ttk.Label(add_window, text="Name:").pack(pady=5)
        name_entry = ttk.Entry(add_window)
        name_entry.pack(pady=5)

        ttk.Label(add_window, text="Cost (€):").pack(pady=5)
        cost_entry = ttk.Entry(add_window)
        cost_entry.pack(pady=5)

        ttk.Label(add_window, text="Vegetarian:").pack(pady=5)
        vegetarian_var = tk.IntVar()
        vegetarian_check = ttk.Checkbutton(add_window, text="Is Vegetarian", variable=vegetarian_var)
        vegetarian_check.pack(pady=5)

        ttk.Label(add_window, text="Vegan:").pack(pady=5)
        vegan_var = tk.IntVar()
        vegan_check = ttk.Checkbutton(add_window, text="Is Vegan", variable=vegan_var)
        vegan_check.pack(pady=5)

        def save_ingredient():
            name = name_entry.get().strip()
            cost_str = cost_entry.get().strip()
            is_vegetarian = vegetarian_var.get()
            is_vegan = vegan_var.get()

            if not name or not cost_str:
                messagebox.showerror("Input Error", "Please fill in all fields.")
                return

            try:
                cost = float(cost_str)
                if cost < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid non-negative cost.")
                return

            try:
                # Insert into ingredient table
                self.cursor.execute(
                    "INSERT INTO ingredient (name, cost, is_vegetarian, is_vegan) VALUES (%s, %s, %s, %s)",
                    (name, cost, is_vegetarian, is_vegan)
                )
                self.connection.commit()
                messagebox.showinfo("Success", f"Ingredient '{name}' added successfully.")
                add_window.destroy()
                self.populate_ingredients()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to add ingredient: {e}")
                logger.error(f"Error adding ingredient: {e}")
                self.connection.rollback()

        ttk.Button(add_window, text="Save", bootstyle="success", command=save_ingredient).pack(pady=20)

    def edit_ingredient(self):
        """Edit the selected ingredient."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select an ingredient to edit.")
            return

        item = self.tree.item(selected[0])['values']
        ingredient_id, name, cost, is_vegetarian, is_vegan = item

        edit_window = tk.Toplevel(self.parent)
        edit_window.title("Edit Ingredient")
        edit_window.geometry("400x400")
        edit_window.grab_set()  # Make the window modal

        ttk.Label(edit_window, text="Name:").pack(pady=5)
        name_entry = ttk.Entry(edit_window)
        name_entry.insert(0, name)
        name_entry.pack(pady=5)

        ttk.Label(edit_window, text="Cost (€):").pack(pady=5)
        cost_entry = ttk.Entry(edit_window)
        cost_entry.insert(0, cost)
        cost_entry.pack(pady=5)

        ttk.Label(edit_window, text="Vegetarian:").pack(pady=5)
        vegetarian_var = tk.IntVar(value=1 if is_vegetarian == "Yes" else 0)
        vegetarian_check = ttk.Checkbutton(edit_window, text="Is Vegetarian", variable=vegetarian_var)
        vegetarian_check.pack(pady=5)

        ttk.Label(edit_window, text="Vegan:").pack(pady=5)
        vegan_var = tk.IntVar(value=1 if is_vegan == "Yes" else 0)
        vegan_check = ttk.Checkbutton(edit_window, text="Is Vegan", variable=vegan_var)
        vegan_check.pack(pady=5)

        def save_changes():
            new_name = name_entry.get().strip()
            new_cost_str = cost_entry.get().strip()
            new_is_vegetarian = vegetarian_var.get()
            new_is_vegan = vegan_var.get()

            if not new_name or not new_cost_str:
                messagebox.showerror("Input Error", "Please fill in all fields.")
                return

            try:
                new_cost = float(new_cost_str)
                if new_cost < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid non-negative cost.")
                return

            try:
                # Update ingredient table
                self.cursor.execute(
                    "UPDATE ingredient SET name = %s, cost = %s, is_vegetarian = %s, is_vegan = %s WHERE ingredient_id = %s",
                    (new_name, new_cost, new_is_vegetarian, new_is_vegan, ingredient_id)
                )
                self.connection.commit()
                messagebox.showinfo("Success", f"Ingredient '{new_name}' updated successfully.")
                edit_window.destroy()
                self.populate_ingredients()

                # After updating ingredient cost, recalculate pizza prices
                self.recalculate_pizza_prices()

            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to update ingredient: {e}")
                logger.error(f"Error updating ingredient: {e}")
                self.connection.rollback()

        ttk.Button(edit_window, text="Save Changes", bootstyle="primary", command=save_changes).pack(pady=20)

    def delete_ingredient(self):
        """Delete the selected ingredient."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select an ingredient to delete.")
            return

        item = self.tree.item(selected[0])['values']
        ingredient_id, name, cost, is_vegetarian, is_vegan = item

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete ingredient '{name}'?")
        if not confirm:
            return

        try:
            # Check if the ingredient is used in any pizza
            self.cursor.execute("SELECT COUNT(*) AS count FROM pizza_ingredient WHERE ingredient_id = %s", (ingredient_id,))
            result = self.cursor.fetchone()
            if result['count'] > 0:
                messagebox.showerror("Deletion Error", f"Cannot delete ingredient '{name}' as it is used in existing pizzas.")
                return

            # Delete from ingredient table
            self.cursor.execute("DELETE FROM ingredient WHERE ingredient_id = %s", (ingredient_id,))
            self.connection.commit()
            messagebox.showinfo("Success", f"Ingredient '{name}' deleted successfully.")
            self.populate_ingredients()

            # After deleting ingredient, recalculate pizza prices
            self.recalculate_pizza_prices()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to delete ingredient: {e}")
            logger.error(f"Error deleting ingredient: {e}")
            self.connection.rollback()

    def refresh(self):
        """Refresh the ingredient list."""
        self.populate_ingredients()

    def recalculate_pizza_prices(self):
        """Recalculate pizza prices based on ingredient costs, profit margin, and TVA."""
        try:
            # Fetch all pizzas
            self.cursor.execute("SELECT pizza_id, profit_margin, vat, base_price FROM pizza")
            pizzas = self.cursor.fetchall()

            for pizza in pizzas:
                pizza_id = pizza['pizza_id']
                profit_margin = pizza['profit_margin']
                vat = pizza['vat']
                base_price = pizza['base_price']

                # Calculate total ingredient cost
                self.cursor.execute("""
                    SELECT SUM(i.cost) AS total_cost
                    FROM pizza_ingredient pi
                    JOIN ingredient i ON pi.ingredient_id = i.ingredient_id
                    WHERE pi.pizza_id = %s
                """, (pizza_id,))
                result = self.cursor.fetchone()
                total_cost = result['total_cost'] if result['total_cost'] else 0.0

                # Calculate final price: (total_cost + base_price) * (1 + profit_margin) * (1 + vat)
                final_price = round((total_cost + base_price) * (1 + profit_margin) * (1 + vat), 2)

                # Update pizza price
                self.cursor.execute(
                    "UPDATE pizza SET price = %s WHERE pizza_id = %s",
                    (final_price, pizza_id)
                )

                # Update corresponding menu_item price
                self.cursor.execute(
                    "UPDATE menu_item SET price = %s WHERE menu_item_id = %s AND type = 'Pizza'",
                    (final_price, pizza_id)
                )

            self.connection.commit()
            logger.info("Recalculated and updated pizza prices based on ingredient costs.")
            messagebox.showinfo("Success", "Pizza prices have been recalculated based on updated ingredient costs.")

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to recalculate pizza prices: {e}")
            logger.error(f"Error recalculating pizza prices: {e}")
            self.connection.rollback()

import tkinter as tk
from tkinter import messagebox  # Import messagebox
import ttkbootstrap as ttk  # Import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from customer_app.database import DatabaseConnection
from customer_app.auth import Auth
from customer_app.menu import Menu
from customer_app.basket import Basket
from customer_app.order import OrderManager
from decimal import Decimal, ROUND_HALF_UP  # Import Decimal and ROUND_HALF_UP
import datetime
import logging
import decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pizza Ordering System - Customer")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)

        # Initialize database connection
        try:
            self.db = DatabaseConnection()
            self.db.connect()
        except Exception as e:
            self.show_error("Database Connection Error", "Failed to connect to the database.")
            self.root.destroy()
            return

        # Initialize other components
        self.auth = Auth(self.db)
        self.menu = Menu(self.db)
        self.order_manager = OrderManager(self.db)
        self.basket = Basket()
        self.logged_in_customer_id = None

        # Fetch menu data
        self.menu.fetch_menu()

        # Initialize UI frames
        self.login_frame = ttk.Frame(self.root)
        self.register_frame = ttk.Frame(self.root)
        self.main_frame = ttk.Frame(self.root)

        # Show login screen initially
        self.show_login_screen()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Handle application closure."""
        self.db.close()
        self.root.destroy()

    def hide_all_frames(self):
        """Hide all frames."""
        for frame in [self.login_frame, self.register_frame, self.main_frame]:
            frame.pack_forget()

    def show_error(self, title, message):
        """Display error messages within the current frame."""
        # This method can be expanded to show errors in a designated area
        logger.error(f"{title}: {message}")

    def show_info(self, frame, message, color="green"):
        """Display informational messages within the given frame."""
        info_label = ttk.Label(frame, text=message, foreground=color, font=("Helvetica", 12, "bold"))
        info_label.pack(pady=5)
        # Remove the message after a certain time
        frame.after(5000, info_label.destroy)

    def show_login_screen(self, message=None):
        """Display the login screen."""
        self.hide_all_frames()
        self.login_frame.pack(fill='both', expand=True)

        # Clear previous widgets
        for widget in self.login_frame.winfo_children():
            widget.destroy()

        # Centered frame
        frame = ttk.Frame(self.login_frame, padding=20)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        # Title
        ttk.Label(frame, text="Login", font=("Helvetica", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        # Username
        ttk.Label(frame, text="Username:", font=("Helvetica", 14)).grid(row=1, column=0, pady=5, sticky='e')
        self.username_entry = ttk.Entry(frame, font=("Helvetica", 14))
        self.username_entry.grid(row=1, column=1, pady=5, padx=10)

        # Password
        ttk.Label(frame, text="Password:", font=("Helvetica", 14)).grid(row=2, column=0, pady=5, sticky='e')
        self.password_entry = ttk.Entry(frame, show="*", font=("Helvetica", 14))
        self.password_entry.grid(row=2, column=1, pady=5, padx=10)

        # Notification Area
        self.login_notification = ttk.Label(frame, text="", font=("Helvetica", 12))
        self.login_notification.grid(row=3, column=0, columnspan=2, pady=5)

        if message:
            self.login_notification.config(text=message, foreground="green")

        # Login Button
        ttk.Button(frame, text="Login", command=self.login, bootstyle="primary").grid(row=4, column=0, columnspan=2, pady=10)

        # Register Button
        ttk.Button(frame, text="Register", command=self.show_register_screen, bootstyle="success").grid(row=5, column=0, columnspan=2, pady=5)

    def show_register_screen(self, message=None):
        """Display the registration screen."""
        self.hide_all_frames()
        self.register_frame.pack(fill='both', expand=True)

        # Clear previous widgets
        for widget in self.register_frame.winfo_children():
            widget.destroy()

        # Scrollable canvas
        canvas = tk.Canvas(self.register_frame)
        scrollbar = ttk.Scrollbar(self.register_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Registration Form
        ttk.Label(scrollable_frame, text="Register", font=("Helvetica", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        fields = [
            ("First Name", "name"),
            ("Last Name", "last_name"),
            ("Gender (Male/Female/Other)", "gender"),
            ("Birthdate (YYYY-MM-DD)", "birthdate"),
            ("Phone Number", "phone_number"),
            ("Address", "address"),
            ("Username", "username"),
            ("Password", "password")
        ]

        self.reg_entries = {}

        for idx, (label_text, key) in enumerate(fields, start=1):
            ttk.Label(scrollable_frame, text=label_text + ":", font=("Helvetica", 14)).grid(row=idx, column=0, pady=5, sticky='e')
            entry = ttk.Entry(scrollable_frame, font=("Helvetica", 14))
            if key == "password":
                entry.config(show="*")
            entry.grid(row=idx, column=1, pady=5, padx=10)
            self.reg_entries[key] = entry

        # Notification Area
        self.register_notification = ttk.Label(scrollable_frame, text="", font=("Helvetica", 12))
        self.register_notification.grid(row=len(fields)+1, column=0, columnspan=2, pady=5)

        if message:
            self.register_notification.config(text=message, foreground="green")

        # Register Button
        ttk.Button(scrollable_frame, text="Register", command=self.register, bootstyle="primary").grid(row=len(fields)+2, column=0, columnspan=2, pady=10)

        # Back Button
        ttk.Button(scrollable_frame, text="Back to Login", command=lambda: self.show_login_screen(), bootstyle="secondary").grid(row=len(fields)+3, column=0, columnspan=2, pady=5)

    def login(self):
        """Handle user login."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.login_notification.config(text="Please enter both username and password.", foreground="red")
            return

        login_result = self.auth.verify_login(username, password)
        if login_result["success"]:
            self.logged_in_customer_id = login_result["customer_id"]
            self.show_main_screen()
            self.login_notification.config(text="")
        else:
            self.login_notification.config(text=login_result.get("message", "Login failed."), foreground="red")

    def register(self):
        """Handle user registration."""
        user_details = {key: entry.get().strip() for key, entry in self.reg_entries.items()}

        # Basic validation
        if not all(user_details.values()):
            self.register_notification.config(text="All fields must be filled out.", foreground="red")
            return

        # Validate birthdate format
        try:
            datetime.datetime.strptime(user_details['birthdate'], '%Y-%m-%d')
        except ValueError:
            self.register_notification.config(text="Birthdate must be in YYYY-MM-DD format.", foreground="red")
            return

        # Validate gender
        if user_details['gender'].capitalize() not in ['Male', 'Female', 'Other']:
            self.register_notification.config(text="Gender must be Male, Female, or Other.", foreground="red")
            return

        registration_result = self.auth.register_user(user_details)
        if registration_result["success"]:
            self.register_notification.config(text=registration_result.get("message", "Registration successful."), foreground="green")
            self.show_login_screen(message="Registration successful. Please log in.")
        else:
            self.register_notification.config(text=registration_result.get("message", "Registration failed."), foreground="red")

    def show_main_screen(self):
        """Display the main application screen after successful login."""
        self.hide_all_frames()
        self.main_frame.pack(fill='both', expand=True)

        # Clear previous widgets
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Notification Area - Placed outside content_frame
        self.main_notification = ttk.Label(self.main_frame, text="", font=("Helvetica", 12))
        self.main_notification.pack(pady=5, side='top', fill='x')

        # Fetch customer details to check birthday
        try:
            query = "SELECT birthdate FROM customer WHERE customer_id = %s"
            cursor = self.db.execute_query(query, (self.logged_in_customer_id,))
            customer = cursor.fetchone()
            if customer:
                today = datetime.date.today()
                birthdate = customer['birthdate']
                if today.month == birthdate.month and today.day == birthdate.day:
                    self.is_birthday = True
                    logger.info("Today is the customer's birthday.")
                else:
                    self.is_birthday = False
            else:
                self.is_birthday = False
        except Exception as e:
            logger.error(f"Error fetching customer birthdate: {e}")
            self.is_birthday = False

        # Side Menu Frame
        side_menu = ttk.Frame(self.main_frame, width=200)
        side_menu.pack(side='left', fill='y')

        # Content Frame
        content = ttk.Frame(self.main_frame)
        content.pack(side='left', fill='both', expand=True)

        # Navigation Buttons
        ttk.Button(side_menu, text="Pizzas", command=lambda: self.show_menu(content, 'Pizza'), bootstyle="success", width=20).pack(pady=10)
        ttk.Button(side_menu, text="Drinks", command=lambda: self.show_menu(content, 'Drink'), bootstyle="success", width=20).pack(pady=10)
        ttk.Button(side_menu, text="Desserts", command=lambda: self.show_menu(content, 'Dessert'), bootstyle="success", width=20).pack(pady=10)
        ttk.Button(side_menu, text="Basket", command=lambda: self.show_basket(content), bootstyle="warning", width=20).pack(pady=10)
        ttk.Button(side_menu, text="Profile", command=lambda: self.show_profile(content), bootstyle="info", width=20).pack(pady=10)
        ttk.Button(side_menu, text="My Orders", command=lambda: self.show_orders(content), bootstyle="info", width=20).pack(pady=10)
        ttk.Button(side_menu, text="Logout", command=self.logout, bootstyle="danger", width=20).pack(pady=10)

        # Initialize with Pizzas menu
        self.show_menu(content, 'Pizza')

    def show_menu(self, content_frame, item_type):
        """Display the menu based on item type."""
        # Clear previous content
        for widget in content_frame.winfo_children():
            widget.destroy()

        # Fetch menu items by type
        menu_items = self.menu.get_menu_items_by_type(item_type)

        if not menu_items:
            ttk.Label(content_frame, text=f"No {item_type}s available.", font=("Helvetica", 16)).pack(pady=20)
            return

        # Create a canvas with scrollbar
        canvas = tk.Canvas(content_frame)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Enable mouse wheel scrolling
        self.enable_mouse_wheel_scrolling(canvas)

        # Display each menu item
        for menu_item_id, details in menu_items.items():
            frame = ttk.Frame(scrollable_frame, borderwidth=2, relief="groove", padding=10)
            frame.pack(pady=10, padx=10, fill='x')

            # Item Name and Base Price
            ttk.Label(frame, text=details['name'], font=("Helvetica", 16, "bold")).grid(row=0, column=0, pady=5, sticky='w')
            ttk.Label(frame, text=f"€{Decimal(details['price']):.2f}", font=("Helvetica", 14)).grid(row=0, column=1, pady=5, sticky='e')

            row_counter = 1  # To keep track of the row number

            # Ingredients (for Pizzas)
            if details['type'].lower() == 'pizza':
                ingredients = ", ".join(details['ingredients'])
                ttk.Label(frame, text=f"Ingredients: {ingredients}", font=("Helvetica", 12), wraplength=400, justify="left").grid(row=row_counter, column=0, columnspan=2, sticky='w', pady=5)
                row_counter += 1

                # Dietary Information
                dietary_info = []
                if details['is_vegetarian']:
                    dietary_info.append("Vegetarian")
                if details['is_vegan']:
                    dietary_info.append("Vegan")

                if dietary_info:
                    ttk.Label(frame, text=" / ".join(dietary_info), font=("Helvetica", 12, "italic"), foreground="green").grid(row=row_counter, column=0, columnspan=2, sticky='w', pady=5)
                    row_counter += 1

            # Quantity Selector
            qty_var = tk.IntVar(value=1)
            ttk.Label(frame, text="Quantity:", font=("Helvetica", 12)).grid(row=row_counter, column=0, pady=5, sticky='e')
            qty_spinbox = ttk.Spinbox(frame, from_=1, to=10, textvariable=qty_var, width=5, font=("Helvetica", 12))
            qty_spinbox.grid(row=row_counter, column=1, pady=5, padx=10, sticky='w')
            row_counter += 1

            # Add to Basket Button
            ttk.Button(
                frame,
                text="Add to Basket",
                command=lambda id_=menu_item_id, name=details['name'], type_=details['type'], qty=qty_var, price=details['price']: self.add_to_basket(id_, name, type_, qty.get(), price),
                bootstyle="success"
            ).grid(row=row_counter, column=0, columnspan=2, pady=5)
            row_counter += 1




    def add_to_basket(self, item_id, name, item_type, quantity, price):
        """Add an item to the basket."""
        if quantity < 1:
            self.main_notification.config(text="Quantity must be at least 1.", foreground="red")
            return
        self.basket.add_item(item_id, name, quantity, item_type, price)
        self.main_notification.config(text=f"Added {quantity} x {name} to basket at €{Decimal(price):.2f} each.", foreground="green")

    def show_basket(self, content_frame):
        """Display the basket contents with detailed price calculations."""
        # Clear previous content
        for widget in content_frame.winfo_children():
            widget.destroy()

        ttk.Label(content_frame, text="Your Basket", font=("Helvetica", 18, "bold")).pack(pady=10)

        if not self.basket.items:
            ttk.Label(content_frame, text="Your basket is empty.", font=("Helvetica", 14)).pack(pady=20)
            return

        # Create a frame to hold items and make it scrollable
        canvas = tk.Canvas(content_frame)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Enable mouse wheel scrolling
        self.enable_mouse_wheel_scrolling(canvas)

        # Create a frame to hold basket items inside scrollable_frame
        items_frame = ttk.Frame(scrollable_frame)
        items_frame.pack(pady=10, padx=20, fill='both', expand=True)

        for item in self.basket.items:
            frame = ttk.Frame(items_frame, borderwidth=2, relief="groove", padding=10)
            frame.pack(pady=5, padx=5, fill='x')

            # Item Name and Quantity
            ttk.Label(frame, text=f"{item['name']} (x{item['quantity']})", font=("Helvetica", 14, "bold")).pack(anchor='w')

            # Price per Item
            ttk.Label(frame, text=f"Price: €{item['price']:.2f}", font=("Helvetica", 12)).pack(anchor='w')

            # Total for this Item
            item_total = (item['price'] * item['quantity']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            ttk.Label(frame, text=f"Total: €{item_total:.2f}", font=("Helvetica", 12)).pack(anchor='w')

            # Delete Button
            ttk.Button(
                frame,
                text="Delete",
                bootstyle="danger",
                width=10,
                command=lambda id_=item['id']: self.delete_basket_item(id_, content_frame)
            ).pack(anchor='e', pady=5)

        # Now, display Calculations outside the scrollable area
        calculations_frame = ttk.Frame(content_frame)
        calculations_frame.pack(pady=10, padx=20, anchor='e')

        # Calculate total price with detailed breakdown
        total_details = self.basket.calculate_total_price()

        subtotal = Decimal(total_details['subtotal'])
        vat_amount = Decimal(total_details['vat_amount'])
        profit = Decimal(total_details['profit'])
        grand_total = Decimal(total_details['grand_total'])

        # Menu prices already include the 40% margin and 9% VAT, so they are not added again
        ttk.Label(calculations_frame, text=f"Subtotal: €{subtotal:.2f}", font=("Helvetica", 14)).pack(anchor='e')

        # If birthday discount was applied, display it
        if getattr(self, 'is_birthday', False) and self.basket.birthday_discount_applied:
            ttk.Label(calculations_frame, text=f"Birthday Discount (10%): -€{subtotal * Decimal('0.10'):.2f}", font=("Helvetica", 14), foreground="green").pack(anchor='e')

        # Also display other discounts
        if self.basket.discount_amount > Decimal('0.00'):
            ttk.Label(calculations_frame, text=f"Discount Applied: -€{self.basket.discount_amount:.2f}", font=("Helvetica", 14), foreground="green").pack(anchor='e')

        ttk.Label(calculations_frame, text=f"Grand Total: €{grand_total:.2f}", font=("Helvetica", 16, "bold")).pack(anchor='e', pady=5)
        ttk.Label(calculations_frame, text=f"incl. VAT (9%): €{vat_amount:.2f}", font=("Helvetica", 11)).pack(anchor='e')

        # Discount Code Entry
        discount_frame = ttk.Frame(content_frame)
        discount_frame.pack(pady=5, anchor='e', padx=20)
        ttk.Label(discount_frame, text="Discount Code:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.discount_entry = ttk.Entry(discount_frame, font=("Helvetica", 14))
        self.discount_entry.pack(side='left', padx=5)
        ttk.Button(discount_frame, text="Apply", command=self.apply_discount, bootstyle="info").pack(side='left', padx=5)

        # Place Order Button
        ttk.Button(content_frame, text="Place Order", command=self.place_order_gui, bootstyle="success", width=20).pack(pady=10)




    def apply_discount(self):
        """Apply discount code to the basket."""
        discount_code = self.discount_entry.get().strip()
        if not discount_code:
            self.main_notification.config(text="Please enter a discount code.", foreground="red")
            return

        # Fetch the total details from the basket's calculate_total_price method
        total_details = self.basket.calculate_total_price()
        subtotal = total_details['subtotal']  # Use 'subtotal' as the base for discounts

        discount_result = self.order_manager.validate_and_apply_discount_code(discount_code, subtotal)

        if discount_result["success"]:
            discount_amount = Decimal(str(discount_result["discount_amount"])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.basket.apply_discount(discount_amount)
            self.basket.discount_code = discount_code      # the order step must not validate it a second time
            new_total = self.basket.calculate_total_price()['grand_total']
            message = f"{discount_result['message']} Discount Applied: -€{discount_amount:.2f} \nNew Total: €{new_total:.2f}"
            self.main_notification.config(text=message, foreground="green")
            
            # Refresh basket to show updated total
            self.show_basket(content_frame=self.main_frame.winfo_children()[-1])  # Assuming basket is the last child
        else:
            self.main_notification.config(text=discount_result.get("message", "Failed to apply discount code."), foreground="red")

    def place_order_gui(self):
        """Handle placing the order via GUI."""
        if not self.basket.items:
            self.main_notification.config(text="Your basket is empty.", foreground="red")
            return

        # Retrieve the discount code before clearing the frame
        discount_code = self.discount_entry.get().strip()

        # Select delivery method within the main content frame
        content = self.main_frame.winfo_children()[-1]
        for widget in content.winfo_children():
            widget.destroy()

        ttk.Label(content, text="Select Delivery Method", font=("Helvetica", 16, "bold")).pack(pady=10)

        delivery_method = tk.StringVar(value='Delivery')
        ttk.Radiobutton(content, text="Delivery", variable=delivery_method, value='Delivery').pack(pady=5)
        ttk.Radiobutton(content, text="Pickup", variable=delivery_method, value='Pickup').pack(pady=5)

        # Confirm Order Button
        ttk.Button(content, text="Confirm Order", command=lambda: self.confirm_order(delivery_method.get(), discount_code), bootstyle="success").pack(pady=20)

    def confirm_order(self, method, discount_code):
        """Confirm and place the order."""
        logger.info(f"Attempting to place order for customer_id={self.logged_in_customer_id}, method={method}, discount_code={discount_code or 'None'}")

        # Check if today is the customer's birthday
        is_birthday = False
        try:
            query = "SELECT birthdate FROM customer WHERE customer_id = %s"
            cursor = self.db.execute_query(query, (self.logged_in_customer_id,))
            customer = cursor.fetchone()
            if customer:
                today = datetime.date.today()
                birthdate = customer['birthdate']
                if today.month == birthdate.month and today.day == birthdate.day:
                    is_birthday = True
        except Exception as e:
            logger.error(f"Error checking birthday: {e}")

        # Pass discount_code if available, otherwise pass None
        order_result = self.order_manager.place_order(
            self.logged_in_customer_id,
            self.basket,
            method,
            discount_code if discount_code else None,  # Handle empty discount code
            is_birthday  # Pass birthday status to order manager
        )

        # Handle the result and display confirmation or error message
        content = self.main_frame.winfo_children()[-1]
        for widget in content.winfo_children():
            widget.destroy()

        if not order_result:
            logger.error("Order result is None.")
            ttk.Label(content, text="An unexpected error occurred while placing your order.", font=("Helvetica", 14), foreground="red").pack(pady=10)
            ttk.Button(content, text="Return to Basket", command=lambda: self.show_basket(content), bootstyle="warning").pack(pady=10)
            return

        if order_result["success"]:
            details = order_result["details"]
            ttk.Label(content, text="Order Confirmation", font=("Helvetica", 18, "bold")).pack(pady=10)

            confirmation_info = f"""Confirmation Number: {details['confirmation_number']}
        Delivery Method: {details['delivery_method']}
        Total Price: €{details['total_price']:.2f}
        Delivery Time: {details['delivery_time_estimation']}
        """

            if details["discount_applied"]:
                confirmation_info += f"Discount Applied: -€{details['discount_amount']:.2f}\n"

            if details["free_pizza"]:
                confirmation_info += "Your 10th pizza: a free pizza was added to this order!\n"

            ttk.Label(content, text=confirmation_info, font=("Helvetica", 14), justify="left").pack(pady=10)

            # Option to return to menu
            ttk.Button(content, text="Return to Menu", command=lambda: self.show_menu(content, 'Pizza'), bootstyle="info").pack(pady=10)

            # Clear the basket
            self.basket.clear_basket()
        else:
            ttk.Label(content, text=order_result.get("message", "Failed to place order."), font=("Helvetica", 14), foreground="red").pack(pady=10)
            # Option to retry
            ttk.Button(content, text="Return to Basket", command=lambda: self.show_basket(content), bootstyle="warning").pack(pady=10)

    def show_profile(self, content_frame):
        """Display and manage the user's profile."""
        # Clear previous content
        for widget in content_frame.winfo_children():
            widget.destroy()

        ttk.Label(content_frame, text="Your Profile", font=("Helvetica", 18, "bold")).pack(pady=10)

        try:
            query = """
                SELECT name, last_name, gender, birthdate, phone_number, address, pizzas_ordered
                FROM customer
                WHERE customer_id = %s
            """
            cursor = self.db.execute_query(query, (self.logged_in_customer_id,))
            customer = cursor.fetchone()
            if not customer:
                ttk.Label(content_frame, text="Customer not found.", font=("Helvetica", 14), foreground="red").pack(pady=10)
                return

            # Profile Information Frame
            frame = ttk.Frame(content_frame, padding=20)
            frame.pack()

            fields = [
                ("First Name", customer['name']),
                ("Last Name", customer['last_name']),
                ("Gender", customer['gender']),
                ("Birthdate (YYYY-MM-DD)", customer['birthdate'].strftime('%Y-%m-%d')),
                ("Phone Number", customer['phone_number']),
                ("Address", customer['address'])
            ]

            self.profile_entries = {}

            for idx, (label_text, value) in enumerate(fields, start=1):
                ttk.Label(frame, text=label_text + ":", font=("Helvetica", 14)).grid(row=idx, column=0, sticky='e', pady=5)
                entry = ttk.Entry(frame, font=("Helvetica", 14))
                entry.grid(row=idx, column=1, pady=5, padx=10)
                entry.insert(0, value)
                self.profile_entries[label_text] = entry

            # Loyalty Status
            pizzas_ordered = customer['pizzas_ordered'] % 10
            ttk.Label(frame, text=f"Pizzas Ordered Towards Free Pizza: {pizzas_ordered}/10", font=("Helvetica", 14, "bold")).grid(row=len(fields)+1, column=0, columnspan=2, pady=10)

            # Calculate Days Until Next Birthday
            today = datetime.date.today()
            birthdate = customer['birthdate']
            next_birthday = birthdate.replace(year=today.year)

            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)

            days_until_birthday = (next_birthday - today).days

            # Birthday Offer Message
            if days_until_birthday == 0:
                birthday_message = "Happy Birthday! You have a free pizza and drink on your order today!"
            else:
                birthday_message = f"{days_until_birthday} day(s) until your birthday! Get a free pizza and drink on your special day."

            ttk.Label(frame, text=birthday_message, font=("Helvetica", 12), foreground="blue").grid(row=len(fields)+2, column=0, columnspan=2, pady=5)

            # Notification Area
            self.profile_notification = ttk.Label(content_frame, text="", font=("Helvetica", 12))
            self.profile_notification.pack(pady=5)

            # Save Changes Button
            ttk.Button(frame, text="Save Changes", command=lambda: self.save_profile_changes(customer, frame), bootstyle="success").grid(row=len(fields)+3, column=0, columnspan=2, pady=10)

        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            ttk.Label(content_frame, text="Failed to retrieve profile information.", font=("Helvetica", 14), foreground="red").pack(pady=10)

    def save_profile_changes(self, customer, frame):
        """Save changes made to the user's profile."""
        updated_details = {
            'name': self.profile_entries["First Name"].get().strip(),
            'last_name': self.profile_entries["Last Name"].get().strip(),
            'gender': self.profile_entries["Gender"].get().strip(),
            'birthdate': self.profile_entries["Birthdate (YYYY-MM-DD)"].get().strip(),
            'phone_number': self.profile_entries["Phone Number"].get().strip(),
            'address': self.profile_entries["Address"].get().strip()
        }

        # Basic validation
        if not all(updated_details.values()):
            self.profile_notification.config(text="All fields must be filled out.", foreground="red")
            return

        # Validate birthdate format
        try:
            datetime.datetime.strptime(updated_details['birthdate'], '%Y-%m-%d')
        except ValueError:
            self.profile_notification.config(text="Birthdate must be in YYYY-MM-DD format.", foreground="red")
            return

        # Validate gender
        if updated_details['gender'].capitalize() not in ['Male', 'Female', 'Other']:
            self.profile_notification.config(text="Gender must be Male, Female, or Other.", foreground="red")
            return

        try:
            update_query = """
                UPDATE customer
                SET name = %s, last_name = %s, gender = %s, birthdate = %s, phone_number = %s, address = %s
                WHERE customer_id = %s
            """
            params = (
                updated_details['name'],
                updated_details['last_name'],
                updated_details['gender'].capitalize(),
                updated_details['birthdate'],
                updated_details['phone_number'],
                updated_details['address'],
                self.logged_in_customer_id
            )
            self.db.execute_query(update_query, params)
            self.db.connection.commit()
            self.profile_notification.config(text="Profile updated successfully.", foreground="green")
            logger.info(f"Customer ID {self.logged_in_customer_id} updated their profile.")
        except Exception as e:
            self.db.connection.rollback()
            logger.error(f"Error updating profile: {e}")
            self.profile_notification.config(text="Failed to update profile.", foreground="red")

    def logout(self):
        """Handle user logout."""
        self.logged_in_customer_id = None
        self.basket.clear_basket()
        self.hide_all_frames()
        self.show_login_screen(message="You have been logged out.")

    def enable_mouse_wheel_scrolling(self, canvas):
        """Enable mouse wheel scrolling for the canvas."""
        def _on_mousewheel(event):
            # Adjust for different platforms: Windows, MacOS, and Linux
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:  # Linux scroll up
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Linux scroll down
                canvas.yview_scroll(1, "units")
        
        # Bind mouse wheel events for different platforms
        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows and MacOS
        canvas.bind_all("<Button-4>", _on_mousewheel)  # Linux scroll up
        canvas.bind_all("<Button-5>", _on_mousewheel)   # Linux scroll down

    def show_orders(self, content_frame):
        """Display the customer's recent orders and allow cancellation if within 5 minutes."""
        # Clear previous content
        for widget in content_frame.winfo_children():
            widget.destroy()

        ttk.Label(content_frame, text="Your Orders", font=("Helvetica", 18, "bold")).pack(pady=10)

        # Fetch customer's recent orders
        try:
            query = """
                SELECT order_id, order_date, confirmation_number, status, total_price
                FROM customerorder
                WHERE customer_id = %s
                ORDER BY order_date DESC
                LIMIT 10
            """
            cursor = self.db.execute_query(query, (self.logged_in_customer_id,))
            orders = cursor.fetchall()

            if not orders:
                ttk.Label(content_frame, text="You have no recent orders.", font=("Helvetica", 14)).pack(pady=20)
                return

            # Create a Treeview to display orders
            columns = ('Order ID', 'Order Date', 'Status', 'Total Price')
            tree = ttk.Treeview(content_frame, columns=columns, show='headings')
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor='center')
            tree.pack(pady=10, padx=20, fill='both', expand=True)

            # Insert orders into the treeview
            for order in orders:
                order_id = order['order_id']
                order_date = order['order_date'].strftime('%Y-%m-%d %H:%M:%S')
                status = order['status']
                total_price = f"€{order['total_price']:.2f}"
                tree.insert('', 'end', values=(order_id, order_date, status, total_price))

            # Bind double-click event to view order details or cancel
            def on_order_select(event):
                selected_item = tree.selection()
                if not selected_item:
                    return
                item = tree.item(selected_item)
                order_id = item['values'][0]
                status = item['values'][2]
                self.show_order_details(content_frame, order_id, status)

            tree.bind("<Double-1>", on_order_select)

        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            ttk.Label(content_frame, text="Failed to retrieve orders.", font=("Helvetica", 14), foreground="red").pack(pady=10)

    def show_order_details(self, content_frame, order_id, status):
        """Display details of the selected order and allow cancellation if possible."""
        # Clear previous content
        for widget in content_frame.winfo_children():
            widget.destroy()

        ttk.Label(content_frame, text=f"Order Details - Order ID {order_id}", font=("Helvetica", 18, "bold")).pack(pady=10)

        # Fetch order items
        try:
            query = """
                SELECT oi.menu_item_id, oi.quantity, mi.name, mi.price
                FROM order_item oi
                JOIN menu_item mi ON oi.menu_item_id = mi.menu_item_id
                WHERE oi.order_id = %s
            """
            cursor = self.db.execute_query(query, (order_id,))
            items = cursor.fetchall()

            if not items:
                ttk.Label(content_frame, text="No items found for this order.", font=("Helvetica", 14)).pack(pady=10)
                return

            # Display order items
            total_price = decimal.Decimal('0.00')
            for item in items:
                item_total = decimal.Decimal(item['price']) * item['quantity']
                total_price += item_total
                item_text = f"{item['quantity']} x {item['name']} @ €{item['price']:.2f} each = €{item_total:.2f}"
                ttk.Label(content_frame, text=item_text, font=("Helvetica", 12)).pack(anchor='w', padx=20)

            ttk.Label(content_frame, text=f"Total Price: €{total_price:.2f}", font=("Helvetica", 14, "bold")).pack(pady=10)

            # Show order status
            ttk.Label(content_frame, text=f"Order Status: {status}", font=("Helvetica", 14, "bold")).pack(pady=5)

            # Check if the order can be cancelled
            if status == 'Pending':
                # Fetch order date
                query = "SELECT order_date FROM customerorder WHERE order_id = %s"
                cursor = self.db.execute_query(query, (order_id,))
                order = cursor.fetchone()
                if order:
                    order_date = order['order_date']
                    now = datetime.datetime.now()
                    time_diff = now - order_date
                    if time_diff.total_seconds() <= 300:  # 5 minutes
                        ttk.Button(content_frame, text="Cancel Order", command=lambda: self.cancel_order(order_id, content_frame), bootstyle="danger").pack(pady=10)
                    else:
                        ttk.Label(content_frame, text="Order can no longer be cancelled.", font=("Helvetica", 12), foreground="red").pack(pady=5)
                else:
                    ttk.Label(content_frame, text="Order date not found.", font=("Helvetica", 12), foreground="red").pack(pady=5)
            else:
                ttk.Label(content_frame, text="Order cannot be cancelled.", font=("Helvetica", 12), foreground="red").pack(pady=5)

            ttk.Button(content_frame, text="Back to Orders", command=lambda: self.show_orders(content_frame), bootstyle="secondary").pack(pady=10)

        except Exception as e:
            logger.error(f"Error fetching order details: {e}")
            ttk.Label(content_frame, text="Failed to retrieve order details.", font=("Helvetica", 14), foreground="red").pack(pady=10)

    def cancel_order(self, order_id, content_frame):
        """Attempt to cancel the order."""
        result = self.order_manager.cancel_order(self.logged_in_customer_id, order_id)
        # Clear previous content
        for widget in content_frame.winfo_children():
            widget.destroy()

        if result["success"]:
            ttk.Label(content_frame, text=result["message"], font=("Helvetica", 14), foreground="green").pack(pady=10)
        else:
            ttk.Label(content_frame, text=result["message"], font=("Helvetica", 14), foreground="red").pack(pady=10)

        ttk.Button(content_frame, text="Back to Orders", command=lambda: self.show_orders(content_frame), bootstyle="secondary").pack(pady=10)

    # [Include any other methods as needed...]

def main():
    root = ttk.Window(themename="flatly")  # Use ttkbootstrap Window
    app = CustomerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

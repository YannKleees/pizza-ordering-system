import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from staff_app.database import create_db_connection
from staff_app.menu_management import MenuManagement
from staff_app.order_history import OrderHistory
from staff_app.real_time_orders import RealTimeOrders
from staff_app.receipts import Receipts
from staff_app.delivery_management import DeliveryManagement
from staff_app.discount_code_manager import DiscountCodeManager
from staff_app.earnings_report import EarningsReport
from staff_app.ingredient_management import IngredientManagement
import logging


# Configure logging
logging.basicConfig(
    filename='staff_app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class StaffApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pizza Ordering System - Staff")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)

        # Initialize database connection
        try:
            self.connection, self.cursor = create_db_connection()
            if not self.connection or not self.cursor:
                raise Exception("Failed to connect to the database.")
        except Exception as e:
            tk.messagebox.showerror("Database Connection Error", str(e))
            logger.error(f"Database connection failed: {e}")
            self.root.destroy()
            return

        # Create the main layout
        self.create_layout()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Handle application closure."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection and self.connection.is_connected():
                self.connection.close()
            logger.info("Database connection closed.")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
        self.root.destroy()

    def create_layout(self):
        """Create the main layout with side menu and content area."""
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True)

        # Side menu
        self.side_menu = ttk.Frame(self.main_frame, width=200)
        self.side_menu.pack(side='left', fill='y')

        # Content area
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(side='right', fill='both', expand=True)

        # Add buttons to side menu
        self.create_side_menu()

        # Initialize frames for different sections
        self.frames = {}
        self.init_frames()

        # Show the default frame (e.g., Menu Management)
        self.show_frame('MenuManagement')

    def create_side_menu(self):
        """Create side menu with buttons."""
        ttk.Label(self.side_menu, text="Navigation", font=("Helvetica", 16, "bold")).pack(pady=10)

        ttk.Button(
            self.side_menu,
            text="Menu Management",
            command=lambda: self.show_frame('MenuManagement'),
            width=20
        ).pack(pady=5)

        ttk.Button(
            self.side_menu,
            text="Order History",
            command=lambda: self.show_frame('OrderHistory'),
            width=20
        ).pack(pady=5)

        ttk.Button(
            self.side_menu,
            text="Real-Time Orders",
            command=lambda: self.show_frame('RealTimeOrders'),
            width=20
        ).pack(pady=5)

        ttk.Button(
            self.side_menu,
            text="Receipts",
            command=lambda: self.show_frame('Receipts'),
            width=20
        ).pack(pady=5)

        ttk.Button(
            self.side_menu,
            text="Delivery Management",
            command=lambda: self.show_frame('DeliveryManagement'),
            width=20
        ).pack(pady=5)

        ttk.Button(
            self.side_menu,
            text="Earnings Report",
            command=lambda: self.show_frame('EarningsReport'),
            width=20
        ).pack(pady=5)

        ttk.Button(
            self.side_menu,
            text="Discount Codes",
            command=lambda: self.show_frame('DiscountCodeManager'),
            width=20
        ).pack(pady=5)

        ttk.Button(
            self.side_menu,
            text="Ingredient Management",  # Added Ingredient Management button
            command=lambda: self.show_frame('IngredientManagement'),
            width=20
        ).pack(pady=5)

    def init_frames(self):
        """Initialize frames for different sections."""
        # Initialize each section frame and store them in a dictionary
        self.frames['MenuManagement'] = ttk.Frame(self.content_frame)
        self.menu_management = MenuManagement(self.frames['MenuManagement'], self.cursor, self.connection)

        self.frames['OrderHistory'] = ttk.Frame(self.content_frame)
        self.order_history = OrderHistory(self.frames['OrderHistory'], self.cursor)

        self.frames['RealTimeOrders'] = ttk.Frame(self.content_frame)
        self.real_time_orders = RealTimeOrders(self.frames['RealTimeOrders'], self.cursor, self.connection)

        self.frames['Receipts'] = ttk.Frame(self.content_frame)
        self.receipts = Receipts(self.frames['Receipts'], self.cursor)

        self.frames['DeliveryManagement'] = ttk.Frame(self.content_frame)
        self.delivery_management = DeliveryManagement(self.frames['DeliveryManagement'], self.cursor, self.connection)

        self.frames['EarningsReport'] = ttk.Frame(self.content_frame)
        self.earnings_report = EarningsReport(self.frames['EarningsReport'], self.cursor, self.connection)

        self.frames['DiscountCodeManager'] = ttk.Frame(self.content_frame)
        self.discount_code_manager = DiscountCodeManager(self.frames['DiscountCodeManager'], self.cursor, self.connection)

        self.frames['IngredientManagement'] = ttk.Frame(self.content_frame)
        self.ingredient_management = IngredientManagement(self.frames['IngredientManagement'], self.cursor, self.connection)

        # Mapping of frame names to their instances
        self.frame_instances = {
            'MenuManagement': self.menu_management,
            'OrderHistory': self.order_history,
            'RealTimeOrders': self.real_time_orders,
            'Receipts': self.receipts,
            'DeliveryManagement': self.delivery_management,
            'EarningsReport': self.earnings_report,
            'DiscountCodeManager': self.discount_code_manager,
            'IngredientManagement': self.ingredient_management  # Added IngredientManagement
        }

        # Hide all frames initially
        for frame in self.frames.values():
            frame.pack_forget()

    def show_frame(self, frame_name):
        """Show the selected frame and hide others."""
        # Hide all frames
        for frame in self.frames.values():
            frame.pack_forget()

        # Show the selected frame
        frame = self.frames[frame_name]
        frame.pack(fill='both', expand=True)

        # Refresh the frame if it has a refresh method
        frame_instance = self.frame_instances.get(frame_name)
        if frame_instance and hasattr(frame_instance, 'refresh'):
            frame_instance.refresh()

    def refresh_current_frame(self):
        """Optional method to refresh the current frame if needed."""
        pass

    def update_delivery_personnel_availability(self):
        """Update delivery personnel availability after 30 minutes."""
        try:
            # Find delivery personnel who became unavailable more than 30 minutes ago
            cutoff_time = datetime.now() - timedelta(minutes=30)
            self.cursor.execute("""
                SELECT da.delivery_person_id
                FROM deliveryassignment da
                WHERE da.assigned_at <= %s
                AND NOT EXISTS (
                    SELECT 1 FROM customerorder co
                    WHERE co.order_id = da.order_id AND co.status != 'Delivered'
                )
            """, (cutoff_time,))
            personnel_to_update = self.cursor.fetchall()

            for person in personnel_to_update:
                delivery_person_id = person['delivery_person_id']
                # Update availability
                self.cursor.execute("""
                    UPDATE deliverypersonnel SET availability = 1 WHERE delivery_person_id = %s
                """, (delivery_person_id,))
                self.connection.commit()
        except Exception as e:
            logger.error(f"Failed to update delivery personnel availability: {e}")
            self.connection.rollback()


def main():
    # Create the main window using ttkbootstrap's Window
    root = ttk.Window(themename="flatly")  # Use ttkbootstrap Window with the desired theme

    # Initialize the StaffApp
    app = StaffApp(root)

    # Start the Tkinter event loop
    root.mainloop()



if __name__ == "__main__":
    main()

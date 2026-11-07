import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import ttk
from .utils import convert_to_datetime
from datetime import datetime
import decimal
import logging
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Configure logging for the module
logging.basicConfig(
    filename='staff_app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

class EarningsReport:
    def __init__(self, parent, cursor, connection):
        self.parent = parent
        self.cursor = cursor
        self.connection = connection
        self.setup_ui()

    def setup_ui(self):
        """Initialize the Earnings Report UI components."""
        self.parent.pack(fill='both', expand=True)

        # Controls Frame for filters
        controls_frame = ttk.Frame(self.parent)
        controls_frame.pack(fill='x', pady=10, padx=10)

        # Date Range Filters
        ttk.Label(controls_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.start_date_entry = ttk.Entry(controls_frame)
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        ttk.Label(controls_frame, text="End Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.end_date_entry = ttk.Entry(controls_frame)
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        # Region Filter
        ttk.Label(controls_frame, text="Region:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.region_entry = ttk.Entry(controls_frame)
        self.region_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        # Gender Filter
        ttk.Label(controls_frame, text="Gender:").grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.gender_combobox = ttk.Combobox(
            controls_frame,
            values=["All", "Male", "Female", "Other"],
            state="readonly"
        )
        self.gender_combobox.grid(row=1, column=3, padx=5, pady=5, sticky='w')
        self.gender_combobox.current(0)

        # Age Filter
        ttk.Label(controls_frame, text="Min Age:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.min_age_entry = ttk.Entry(controls_frame)
        self.min_age_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        ttk.Label(controls_frame, text="Max Age:").grid(row=2, column=2, padx=5, pady=5, sticky='e')
        self.max_age_entry = ttk.Entry(controls_frame)
        self.max_age_entry.grid(row=2, column=3, padx=5, pady=5, sticky='w')

        # Generate Report Button (moved under the filters)
        generate_button = ttk.Button(
            controls_frame,
            text="Generate Report",
            bootstyle="primary",
            command=self.generate_report
        )
        generate_button.grid(row=3, column=0, columnspan=4, pady=10)

        # Bind events to automatically generate report when inputs change
        self.start_date_entry.bind("<Return>", lambda event: self.generate_report())
        self.end_date_entry.bind("<Return>", lambda event: self.generate_report())
        self.region_entry.bind("<Return>", lambda event: self.generate_report())
        self.gender_combobox.bind("<<ComboboxSelected>>", lambda event: self.generate_report())
        self.min_age_entry.bind("<Return>", lambda event: self.generate_report())
        self.max_age_entry.bind("<Return>", lambda event: self.generate_report())

        # Notebook to hold Table and Graph tabs
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill='both', expand=True)

        # Tabs
        self.table_tab = ttk.Frame(self.notebook)
        self.graph_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.table_tab, text='Table View')
        self.notebook.add(self.graph_tab, text='Graph View')

        # Canvas for table scrolling
        self.canvas = tk.Canvas(self.table_tab)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.table_tab, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Inner Frame for table
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')

        # Configure scroll region
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Enable mouse wheel scrolling
        self.enable_mouse_wheel_scrolling()

        # Generate initial report
        self.generate_report()


    def enable_mouse_wheel_scrolling(self):
        """Enable mouse wheel scrolling for the canvas."""
        def _on_mousewheel(event):
            # Adjust for different platforms
            if event.delta:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:  # Linux scroll up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Linux scroll down
                self.canvas.yview_scroll(1, "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows and MacOS
        self.canvas.bind_all("<Button-4>", _on_mousewheel)    # Linux scroll up
        self.canvas.bind_all("<Button-5>", _on_mousewheel)    # Linux scroll down

    def generate_report(self):
        """Fetch and display the earnings report based on filters."""
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        region = self.region_entry.get().strip()
        gender = self.gender_combobox.get()
        min_age_str = self.min_age_entry.get().strip()
        max_age_str = self.max_age_entry.get().strip()

        # Set default dates if not provided
        if not start_date:
            start_date = '1900-01-01'  # Earliest possible date
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')  # Today's date

        # Validate date inputs
        if not self.validate_date(start_date) or not self.validate_date(end_date):
            messagebox.showerror("Input Error", "Please enter valid dates in YYYY-MM-DD format.")
            return

        # Validate age inputs
        min_age = None
        max_age = None
        if min_age_str:
            try:
                min_age = int(min_age_str)
                if min_age < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid non-negative integer for Min Age.")
                return

        if max_age_str:
            try:
                max_age = int(max_age_str)
                if max_age < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid non-negative integer for Max Age.")
                return

        # Build the SQL query with filters
        query = """
            SELECT co.order_id, co.order_date, c.name, c.gender, c.birthdate, c.address, co.total_price
            FROM customerorder co
            JOIN customer c ON co.customer_id = c.customer_id
            WHERE DATE(co.order_date) BETWEEN %s AND %s
        """
        params = [start_date, end_date]

        if region:
            query += " AND c.address LIKE %s"
            params.append(f"%{region}%")

        if gender != "All":
            query += " AND c.gender = %s"
            params.append(gender)

        if min_age is not None or max_age is not None:
            query += " AND c.birthdate IS NOT NULL"

        try:
            self.cursor.execute(query, tuple(params))
            records = self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to generate earnings report: {e}")
            messagebox.showerror("Database Error", f"Failed to generate report: {e}")
            return

        # Filter by age
        if min_age is not None or max_age is not None:
            today = datetime.today()
            filtered_records = []
            for record in records:
                birthdate = record['birthdate']
                if birthdate:
                    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
                    if min_age is not None and age < min_age:
                        continue
                    if max_age is not None and age > max_age:
                        continue
                    record['age'] = age
                    filtered_records.append(record)
                else:
                    # Exclude records without birthdate when age filtering is applied
                    continue
            records = filtered_records

        logger.info(f"Generated earnings report with {len(records)} records.")
        self.display_report(records)
        self.display_graph(records)


    def validate_date(self, date_str):
        """Validate the date format YYYY-MM-DD."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def display_report(self, records):
        """Display the earnings report in the UI."""
        # Clear the frame
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        if not records:
            ttk.Label(
                self.inner_frame,
                text="No records found for the given criteria.",
                font=("Helvetica", 12)
            ).pack(pady=10)
            return

        # Create table headers
        headers = ["Order ID", "Order Date", "Customer Name", "Gender", "Age", "Address", "Total Earnings (€)"]
        for idx, header in enumerate(headers):
            ttk.Label(
                self.inner_frame,
                text=header,
                font=("Helvetica", 12, "bold")
            ).grid(row=0, column=idx, padx=10, pady=5, sticky='w')

        # Populate table with records
        total_earnings = 0
        for row_idx, record in enumerate(records, start=1):
            order_id = record['order_id']
            order_date = convert_to_datetime(record['order_date']).strftime('%Y-%m-%d %H:%M:%S')
            customer_name = record['name']
            gender = record['gender']
            age = record.get('age', 'N/A')
            address = record['address']
            total_price = record['total_price'] if record['total_price'] else 0.00
            total_earnings += total_price

            ttk.Label(self.inner_frame, text=order_id).grid(row=row_idx, column=0, padx=10, pady=2, sticky='w')
            ttk.Label(self.inner_frame, text=order_date).grid(row=row_idx, column=1, padx=10, pady=2, sticky='w')
            ttk.Label(self.inner_frame, text=customer_name).grid(row=row_idx, column=2, padx=10, pady=2, sticky='w')
            ttk.Label(self.inner_frame, text=gender).grid(row=row_idx, column=3, padx=10, pady=2, sticky='w')
            ttk.Label(self.inner_frame, text=age).grid(row=row_idx, column=4, padx=10, pady=2, sticky='w')
            ttk.Label(self.inner_frame, text=address).grid(row=row_idx, column=5, padx=10, pady=2, sticky='w')
            ttk.Label(self.inner_frame, text=f"€{total_price:.2f}").grid(row=row_idx, column=6, padx=10, pady=2, sticky='w')

        # Summary Section
        ttk.Label(
            self.inner_frame,
            text=f"\nTotal Earnings: €{total_earnings:.2f}",
            font=("Helvetica", 14, "bold")
        ).grid(row=row_idx + 1, column=0, columnspan=7, pady=10, sticky='w')

    def display_graph(self, records):
        """Display earnings data as graphs."""
        # Clear the graph tab
        for widget in self.graph_tab.winfo_children():
            widget.destroy()

        if not records:
            ttk.Label(
                self.graph_tab,
                text="No data available for graphs.",
                font=("Helvetica", 12)
            ).pack(pady=10)
            return

        # Prepare data for the graph
        dates = [convert_to_datetime(record['order_date']).date() for record in records]
        earnings = [record['total_price'] for record in records]

        # Aggregate earnings by date
        earnings_by_date = {}
        for date, earning in zip(dates, earnings):
            if date in earnings_by_date:
                earnings_by_date[date] += earning
            else:
                earnings_by_date[date] = earning

        # Sort the dates
        sorted_dates = sorted(earnings_by_date.keys())
        sorted_earnings = [earnings_by_date[date] for date in sorted_dates]

        # Create the figure and plot
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(sorted_dates, sorted_earnings, marker='o', linestyle='-', color='blue')
        ax.set_title('Earnings Over Time')
        ax.set_xlabel('Date')
        ax.set_ylabel('Total Earnings (€)')
        ax.grid(True)

        # Create a canvas to display the plot
        canvas = FigureCanvasTkAgg(fig, master=self.graph_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

        # Optional: Include a bar chart for gender distribution
        self.display_gender_distribution(records)

    def display_gender_distribution(self, records):
        """Display a pie chart of earnings distribution by gender."""
        # Aggregate earnings by gender
        earnings_by_gender = {}
        for record in records:
            gender = record['gender']
            total_price = record['total_price']
            if gender in earnings_by_gender:
                earnings_by_gender[gender] += total_price
            else:
                earnings_by_gender[gender] = total_price

        # Create the figure and plot
        fig, ax = plt.subplots(figsize=(6, 6))
        genders = list(earnings_by_gender.keys())
        earnings = [earnings_by_gender[gender] for gender in genders]
        ax.pie(earnings, labels=genders, autopct='%1.1f%%', startangle=140)
        ax.set_title('Earnings Distribution by Gender')

        # Create a canvas to display the plot
        canvas = FigureCanvasTkAgg(fig, master=self.graph_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)


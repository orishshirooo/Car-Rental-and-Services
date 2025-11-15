from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QMessageBox
from PyQt6.QtGui import QIcon

# Import from our other .py files in 'src'
from .utils import load_icon
from .database import DBManager
from .manager import RentalManager

# Import all our widgets from the single 'widgets.py' file
from .widgets import (
    AuthWidget,
    VehicleListWidget,
    OptionsWidget,
    ReceiptWidget,
    AdminDashboardWidget,
    MessageWidget,
    SidebarWidget
)


class RentalApp(QMainWindow):
    def __init__(self):
        super().__init__();
        self.setWindowTitle("Ragadio's Car Rentals")

        icon = load_icon("ragadio logo")
        if not icon.isNull():
            self.setWindowIcon(icon)

        # --- SIZES (Standardized) ---
        self.vehicle_list_size = (950, 850);
        self.options_size = (950, 850)
        self.message_size = (950, 850);
        self.admin_size = (950, 850);
        self.login_size = (950, 850)
        self.setMinimumSize(500, 400)

        # --- Initialize Core Components ---
        self.db = DBManager();
        self.manager = RentalManager(self.db)

        # --- Setup Main Layout ---
        container = QWidget();
        layout = QHBoxLayout(container);
        layout.setContentsMargins(0, 0, 0, 0);
        layout.setSpacing(0)
        self.sidebar = SidebarWidget();
        self.sidebar.hide();
        layout.addWidget(self.sidebar)
        self.stack = QStackedWidget();
        layout.addWidget(self.stack);
        self.setCentralWidget(container)

        self.init_widgets();
        self.setup_connections()

    def init_widgets(self):
        # Create instances of our widgets (all imported from widgets.py)
        self.auth_w = AuthWidget(self.manager);
        self.vehicle_list_w = VehicleListWidget(self.manager)
        self.options_w = OptionsWidget(self.manager);
        self.receipt_w = ReceiptWidget()
        self.admin_dashboard_w = AdminDashboardWidget(self.manager);
        self.message_w = MessageWidget(self.manager)

        # Add all widgets to the main stack
        for w in [self.auth_w, self.vehicle_list_w, self.options_w, self.receipt_w, self.admin_dashboard_w,
                  self.message_w]:
            self.stack.addWidget(w)

        self.stack.setCurrentWidget(self.auth_w)
        self.resize(*self.login_size)

    def setup_connections(self):
        # Auth connections
        self.auth_w.customer_login_successful.connect(self.on_customer_login);
        self.auth_w.admin_login_successful.connect(self.on_admin_login);

        # Sidebar connections
        self.sidebar.logout_requested.connect(self.on_logout);
        self.sidebar.vehicle_list_requested.connect(self.go_to_vehicle_list)
        self.sidebar.message_center_requested.connect(self.go_to_message_center)

        # Customer flow connections
        self.vehicle_list_w.proceed_requested.connect(self.go_to_options);
        self.options_w.booking_confirmed.connect(self.on_booking_confirmed)
        self.options_w.back_to_vehicles.connect(self.go_to_vehicle_list);
        self.receipt_w.start_new_rental.connect(self.go_to_vehicle_list)

        # Admin connections (to refresh customer UI)
        self.admin_dashboard_w.signout_requested.connect(self.on_logout)
        self.admin_dashboard_w.availability_updated.connect(self.refresh_customer_vehicle_list_in_background)
        self.admin_dashboard_w.services_updated.connect(self.refresh_customer_options_in_background)

        # Message widget connections
        self.message_w.message_sent.connect(self.on_message_sent);
        self.message_w.back_to_main.connect(self.go_to_vehicle_list)

    # --- SLOTS (Functions that respond to signals) ---

    def refresh_customer_vehicle_list_in_background(self):
        self.vehicle_list_w.update_car_list()

    def refresh_customer_options_in_background(self):
        self.options_w.refresh_services_list()

    def on_customer_login(self, name, email):
        self.vehicle_list_w.update_welcome_message(name);
        self.go_to_vehicle_list();
        self.sidebar.show()

    def on_logout(self):
        self.manager.logout();
        self.auth_w.reset_view()
        self.stack.setCurrentWidget(self.auth_w);
        self.resize(*self.login_size)
        self.sidebar.hide()

    def go_to_vehicle_list(self):
        self.vehicle_list_w.update_car_list()
        self.stack.setCurrentWidget(self.vehicle_list_w);
        self.resize(*self.vehicle_list_size)

    def go_to_options(self, car):
        self.options_w.update_view(car);
        self.stack.setCurrentWidget(self.options_w);
        self.resize(*self.options_size)

    def go_to_message_center(self):
        user = self.manager.current_user
        self.message_w.set_user_details(user.get('name'), user.get('email'));
        self.stack.setCurrentWidget(self.message_w)
        self.resize(*self.message_size)

    def on_booking_confirmed(self, data):
        self.manager.record_transaction(data);
        self.receipt_w.update_receipt(self.manager.current_user['name'], data)
        self.stack.setCurrentWidget(self.receipt_w);
        self.resize(950, 850)  # Standardized size

    def on_message_sent(self):
        QMessageBox.information(self, "Message Sent",
                                "Thank you for your message! Our team will get back to you shortly.")
        self.go_to_vehicle_list()

    def on_admin_login(self):
        self.resize(*self.admin_size)
        self.manager.current_user = {"id": 0, "name": "Administrator", "email": "admin@gmail.com"}

        # Refresh all admin tabs
        self.admin_dashboard_w.sales_tab.handle_reset()
        self.admin_dashboard_w.inventory_tab.populate_availability_table()
        self.admin_dashboard_w.messages_tab.populate_message_table()
        self.admin_dashboard_w.inventory_tab.populate_categories_dropdown()
        self.admin_dashboard_w.inventory_tab.populate_services_table()

        self.sidebar.hide()
        self.stack.setCurrentWidget(self.admin_dashboard_w)

    def closeEvent(self, e):
        # Gracefully close the database connection
        print("Closing database connection...")
        self.db.close();
        super().closeEvent(e)
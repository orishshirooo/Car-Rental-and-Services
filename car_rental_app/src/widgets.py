#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget,
    QGridLayout, QMessageBox, QGroupBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
    QScrollArea, QTextEdit, QSpacerItem, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIntValidator, QPixmap, QIcon, QDoubleValidator

# Relative imports from other files in the 'src' folder
from .utils import format_peso, load_pixmap, load_icon


# --- 1. Base Class ---

class BaseWidget(QWidget):
    def __init__(self):
        super().__init__()

    def create_label(self, text, bold=False, size=12):
        lbl = QLabel(text)
        if bold:
            lbl.setFont(QFont("Arial", size, QFont.Weight.Bold))
        return lbl


# --- 2. Auth Widgets ---

class LoginWidget(BaseWidget):
    customer_login_successful = pyqtSignal(str, str)
    register_requested = pyqtSignal()
    admin_login_successful = pyqtSignal()

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self);
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter);
        layout.setSpacing(15)

        layout.addWidget(self.create_label("Customer Login", True, 18), alignment=Qt.AlignmentFlag.AlignCenter)

        self.email_in = QLineEdit();
        self.email_in.setPlaceholderText("Email Address");
        self.email_in.setMinimumWidth(300)
        self.password_in = QLineEdit();
        self.password_in.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_in.setPlaceholderText("Password");
        self.password_in.setMinimumWidth(300)
        self.password_in.returnPressed.connect(self.handle_login)

        login_btn = QPushButton("Log In");
        login_btn.clicked.connect(self.handle_login)

        signup_lbl = QLabel("<a href='#'>Don't have an account? Sign Up</a>");
        signup_lbl.linkActivated.connect(self.register_requested.emit)

        auth_box = QGroupBox();
        auth_box.setLayout(QVBoxLayout())
        auth_box.layout().addWidget(QLabel("Email:"));
        auth_box.layout().addWidget(self.email_in)
        auth_box.layout().addWidget(QLabel("Password:"));
        auth_box.layout().addWidget(self.password_in)
        auth_box.layout().setContentsMargins(50, 10, 50, 10);
        auth_box.setTitle("Login Credentials")

        layout.addWidget(auth_box, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(login_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(signup_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

    def handle_login(self):
        email, password = self.email_in.text().strip(), self.password_in.text()
        if not (email and password):
            QMessageBox.warning(self, "Error", "Please enter both email and password.")
            return

        if email.lower() == "admin@gmail.com" and password == "admin123":
            self.admin_login_successful.emit()
            self.email_in.clear()
            self.password_in.clear()

        elif self.manager.login(email, password):
            self.customer_login_successful.emit(self.manager.current_user['name'], email)
            self.email_in.clear()
            self.password_in.clear()

        else:
            QMessageBox.critical(self, "Login Failed", "Invalid email or password.")
            self.password_in.clear()


class SignupWidget(BaseWidget):
    registration_successful = pyqtSignal(str, str)
    login_requested = pyqtSignal()

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self);
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter);
        layout.setSpacing(15)

        layout.addWidget(self.create_label("Create Account", True, 18), alignment=Qt.AlignmentFlag.AlignCenter)

        self.name_in = QLineEdit();
        self.name_in.setPlaceholderText("Full Name")
        self.email_in = QLineEdit();
        self.email_in.setPlaceholderText("Email Address")
        self.password_in = QLineEdit();
        self.password_in.setEchoMode(QLineEdit.EchoMode.Password);
        self.password_in.setPlaceholderText("Password")
        self.confirm_password_in = QLineEdit();
        self.confirm_password_in.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_in.setPlaceholderText("Confirm Password");
        self.confirm_password_in.returnPressed.connect(self.handle_signup)

        signup_btn = QPushButton("Sign Up");
        signup_btn.clicked.connect(self.handle_signup)
        login_lbl = QLabel("<a href='#'>Already have an account? Log In</a>");
        login_lbl.linkActivated.connect(self.login_requested.emit)

        auth_box = QGroupBox();
        form_layout = QGridLayout()
        form_layout.addWidget(QLabel("Name:"), 0, 0);
        form_layout.addWidget(self.name_in, 0, 1)
        form_layout.addWidget(QLabel("Email:"), 1, 0);
        form_layout.addWidget(self.email_in, 1, 1)
        form_layout.addWidget(QLabel("Password:"), 2, 0);
        form_layout.addWidget(self.password_in, 2, 1)
        form_layout.addWidget(QLabel("Confirm:"), 3, 0);
        form_layout.addWidget(self.confirm_password_in, 3, 1)

        auth_box.setLayout(form_layout);
        auth_box.setTitle("Registration Details")

        layout.addWidget(auth_box, alignment=Qt.AlignmentFlag.AlignCenter);
        layout.addWidget(signup_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(login_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        for widget in [self.name_in, self.email_in, self.password_in, self.confirm_password_in]:
            widget.setMinimumWidth(250)

    def handle_signup(self):
        name = self.name_in.text().strip();
        email = self.email_in.text().strip()
        password = self.password_in.text();
        confirm_password = self.confirm_password_in.text()

        if not (name and email and password and confirm_password):
            QMessageBox.warning(self, "Error", "Please fill in all fields.");
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            self.password_in.clear();
            self.confirm_password_in.clear();
            return

        result = self.manager.register(name, email, password)

        if result is True:
            QMessageBox.information(self, "Success", "Registration successful! You can now log in.")
            self.login_requested.emit()
            self.name_in.clear();
            self.email_in.clear();
            self.password_in.clear();
            self.confirm_password_in.clear()
        elif "Email already registered." in result:
            QMessageBox.warning(self, "Error", "This email is already registered. Please log in.")
        else:
            QMessageBox.critical(self, "Error", f"Registration failed: {result}")


class AuthWidget(BaseWidget):
    customer_login_successful = pyqtSignal(str, str)
    admin_login_successful = pyqtSignal()

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.stack = QStackedWidget()
        self.login_w = LoginWidget(manager)
        self.signup_w = SignupWidget(manager)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self);
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel()
        pixmap = load_pixmap("ragadio logo", 150, 150)
        if pixmap.isNull():
            logo.setText("🚗");
            logo.setFont(QFont("Arial", 48))
        else:
            logo.setPixmap(pixmap)

        logo.setAlignment(Qt.AlignmentFlag.AlignCenter);
        logo.setStyleSheet("margin-bottom: 20px; background-color: transparent;")

        header = self.create_label("Ragadio's Car Rentals", True, 20)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(self.login_w);
        self.stack.addWidget(self.signup_w)

        self.login_w.register_requested.connect(lambda: self.stack.setCurrentWidget(self.signup_w))
        self.signup_w.login_requested.connect(lambda: self.stack.setCurrentWidget(self.login_w))

        self.login_w.customer_login_successful.connect(self.customer_login_successful.emit)
        self.login_w.admin_login_successful.connect(self.admin_login_successful.emit)

        layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter);
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stack, alignment=Qt.AlignmentFlag.AlignCenter)

    def reset_view(self):
        self.stack.setCurrentWidget(self.login_w)
        self.login_w.email_in.clear();
        self.login_w.password_in.clear()
        self.signup_w.name_in.clear();
        self.signup_w.email_in.clear();
        self.signup_w.password_in.clear();
        self.signup_w.confirm_password_in.clear()


# --- 3. Customer Widgets ---

class VehicleListWidget(BaseWidget):
    proceed_requested = pyqtSignal(object)

    def __init__(self, rental_manager):
        super().__init__()
        self.car_checkboxes = [];
        self.manager = rental_manager
        self.setup_ui();
        self.update_car_list()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.welcome_lbl = self.create_label("", True, 20)
        self.welcome_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_lbl.setStyleSheet("margin-bottom: 5px;")
        main_layout.addWidget(self.welcome_lbl)

        self.scroll_area = QScrollArea();
        self.scroll_area.setWidgetResizable(True)
        self.cars_content_widget = QWidget();
        self.cars_layout = QVBoxLayout(self.cars_content_widget)
        self.cars_layout.setAlignment(Qt.AlignmentFlag.AlignTop);
        self.scroll_area.setWidget(self.cars_content_widget)
        main_layout.addWidget(self.scroll_area)

        proceed_btn = QPushButton("Proceed to Options");
        proceed_btn.clicked.connect(self.proceed_to_options)
        main_layout.addWidget(proceed_btn)

    def enforce_single_selection(self, clicked_checkbox):
        if clicked_checkbox.isChecked():
            for cb in self.car_checkboxes:
                if cb is not clicked_checkbox and cb.isChecked(): cb.setChecked(False)

    def update_car_list(self):
        while self.cars_layout.count():
            item = self.cars_layout.takeAt(0)
            if widget := item.widget(): widget.deleteLater()

        self.car_checkboxes.clear();
        categories = self.manager.get_categories()
        all_cars = self.manager.db.get_all_cars_data(only_available=True)

        if not all_cars:
            self.cars_layout.addWidget(self.create_label("No vehicles currently available for rent.", True),
                                       alignment=Qt.AlignmentFlag.AlignCenter)
            self.cars_layout.addStretch(1);
            return

        for cat in categories:
            group = QGroupBox(cat['name']);
            group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            group_layout = QVBoxLayout(group)
            cars = self.manager.get_cars(cat['id'])

            if cars:
                for car in cars:
                    checkbox = QCheckBox(f"{car.name} - {format_peso(car.price_per_day)} / day")
                    checkbox.setProperty("car_object", car);
                    group_layout.addWidget(checkbox)
                    self.car_checkboxes.append(checkbox)
                    checkbox.clicked.connect(lambda checked, btn=checkbox: self.enforce_single_selection(btn))
                self.cars_layout.addWidget(group)

        self.cars_layout.addStretch(1)

    def update_welcome_message(self, name):
        self.welcome_lbl.setText(f"Welcome, {name}!")

    def proceed_to_options(self):
        selected_checkbox = next((cb for cb in self.car_checkboxes if cb.isChecked()), None)
        if not selected_checkbox:
            QMessageBox.warning(self, "Error", "Please select a car to continue.");
            return

        self.proceed_requested.emit(selected_checkbox.property("car_object"))


class OptionsWidget(BaseWidget):
    booking_confirmed = pyqtSignal(dict)
    back_to_vehicles = pyqtSignal()

    def __init__(self, rental_manager):
        super().__init__();
        self.manager = rental_manager
        self.selected_car = None;
        self.svc_boxes = [];
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.car_selection_label = self.create_label("Options for...", True, 16);
        self.car_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.car_selection_label)

        scroll = QScrollArea();
        scroll.setWidgetResizable(True)
        content_widget = QWidget();
        options_layout_container = QVBoxLayout(content_widget)

        options_group = QGroupBox("Booking Options");
        options_layout = QVBoxLayout();
        options_group.setLayout(options_layout)

        dur_layout = QHBoxLayout();
        self.dur_in = QLineEdit("1");
        self.dur_in.setValidator(QIntValidator(1, 365))
        self.dur_in.setMaximumWidth(60)
        dur_layout.addWidget(QLabel("Duration (days):"));
        dur_layout.addWidget(self.dur_in)
        dur_layout.addStretch();
        options_layout.addLayout(dur_layout)

        self.addons_group = QGroupBox("Add-ons");
        self.addons_layout = QVBoxLayout();
        self.addons_group.setLayout(self.addons_layout)

        self.refresh_services_list()  # Populate for the first time

        options_layout_container.addWidget(options_group);
        options_layout_container.addWidget(self.addons_group)

        options_layout_container.addStretch(1);
        scroll.setWidget(content_widget);
        main_layout.addWidget(scroll)

        confirm_btn = QPushButton("Confirm Booking");
        confirm_btn.clicked.connect(self.confirm_and_book);
        main_layout.addWidget(confirm_btn)
        back_btn = QPushButton("← Back to Car Selection");
        back_btn.clicked.connect(self.back_to_vehicles.emit);
        main_layout.addWidget(back_btn)

    def refresh_services_list(self):
        """Clears and repopulates the add-ons checkboxes."""
        # Clear existing widgets
        while self.addons_layout.count():
            item = self.addons_layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()

        self.svc_boxes.clear()  # Clear the list

        # Repopulate
        for svc in self.manager.get_services():
            # Use bool(svc['is_daily']) since SQLite returns 0 or 1
            price_text = f"{format_peso(svc['price'])} / day" if bool(svc['is_daily']) else format_peso(svc['price'])
            box = QCheckBox(f"{svc['name']} ({price_text})");
            box.setProperty("svc_data", svc)
            self.addons_layout.addWidget(box);
            self.svc_boxes.append(box)

    def update_view(self, car):
        self.selected_car = car;
        self.car_selection_label.setText(f"Options for: {self.selected_car.name}")
        self.dur_in.setText("1");
        for box in self.svc_boxes: box.setChecked(False)

    def confirm_and_book(self):
        if not self.selected_car: return
        days_str = self.dur_in.text()
        if not days_str.isdigit() or int(days_str) <= 0:
            QMessageBox.warning(self, "Error", "Please enter a valid number of days.");
            return
        days = int(days_str);
        base_total = self.selected_car.price_per_day * days
        services = [];
        services_total = 0
        for box in self.svc_boxes:
            if box.isChecked():
                svc = box.property("svc_data")
                cost = svc['price'] * days if bool(svc['is_daily']) else svc['price']
                services_total += cost
                services.append({"name": svc['name'], "cost": cost})
        final_total = base_total + services_total
        booking_data = {"car": self.selected_car, "duration": days, "base_total": base_total,
                        "services": services, "final_total": final_total}
        self.booking_confirmed.emit(booking_data)


class MessageWidget(BaseWidget):
    message_sent = pyqtSignal()
    back_to_main = pyqtSignal()

    def __init__(self, rental_manager):
        super().__init__();
        self.manager = rental_manager;
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self);
        layout.setContentsMargins(20, 20, 20, 20);
        layout.setSpacing(10)
        layout.addWidget(self.create_label("Contact Customer Service", True, 18),
                         alignment=Qt.AlignmentFlag.AlignCenter)

        form_box = QGroupBox("Your Message")
        form_layout = QGridLayout(form_box);
        form_layout.setSpacing(15)
        form_layout.addWidget(QLabel("Your Name:"), 0, 0);
        self.name_in = QLineEdit();
        self.name_in.setReadOnly(True)
        form_layout.addWidget(self.name_in, 0, 1)
        form_layout.addWidget(QLabel("Your Email:"), 1, 0);
        self.email_in = QLineEdit();
        self.email_in.setReadOnly(True)
        form_layout.addWidget(self.email_in, 1, 1)
        form_layout.addWidget(QLabel("Message:"), 2, 0, alignment=Qt.AlignmentFlag.AlignTop);
        self.message_in = QTextEdit()
        self.message_in.setPlaceholderText("Please type your question or concern here...");
        self.message_in.setMinimumHeight(150)
        form_layout.addWidget(self.message_in, 2, 1);
        layout.addWidget(form_box)

        button_layout = QHBoxLayout();
        button_layout.addStretch(1)
        send_btn = QPushButton("Send Message");
        send_btn.clicked.connect(self.send_message)
        back_btn = QPushButton("← Back");
        back_btn.clicked.connect(self.back_to_main.emit)

        button_layout.addWidget(back_btn);
        button_layout.addWidget(send_btn);
        layout.addLayout(button_layout)

    def set_user_details(self, name, email):
        self.name_in.setText(name);
        self.email_in.setText(email);
        self.message_in.clear()

    def send_message(self):
        name = self.name_in.text();
        email = self.email_in.text()
        message = self.message_in.toPlainText().strip()

        if not message:
            QMessageBox.warning(self, "Empty Message", "Please type a message before sending.");
            return

        try:
            self.manager.save_message(name, email, message);
            self.message_sent.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not send message: {e}")


class ReceiptWidget(BaseWidget):
    start_new_rental = pyqtSignal()

    def __init__(self):
        super().__init__();
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self);
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        container = QGroupBox("Booking Confirmed")
        container_layout = QVBoxLayout(container)

        header = QHBoxLayout();
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo = QLabel()
        pixmap = load_pixmap("car-removebg-preview.png", 50, 50)
        if pixmap.isNull():
            logo.setText("🚗");
            logo.setFont(QFont("Arial", 20))
        else:
            logo.setPixmap(pixmap)
        logo.setStyleSheet("background-color: transparent;")

        header.addWidget(logo);
        header.addWidget(self.create_label("BOOKING CONFIRMED", True, 15));
        container_layout.addLayout(header)
        container_layout.addWidget(self.create_label("--- Transaction Details ---", True, 10),
                                   alignment=Qt.AlignmentFlag.AlignCenter)

        scroll_area = QScrollArea();
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget();
        content_layout = QVBoxLayout(content_widget)

        grid = QGridLayout();
        grid.setSpacing(8)
        self.name_lbl = self.create_label("");
        grid.addWidget(self.name_lbl, 0, 0, 1, 2)
        grid.addWidget(QLabel("Car Model:"), 1, 0);
        self.car_lbl = QLabel();
        grid.addWidget(self.car_lbl, 1, 1, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(QLabel("Rental Days:"), 2, 0);
        self.dur_lbl = QLabel();
        grid.addWidget(self.dur_lbl, 2, 1, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(QLabel("Base Cost:"), 3, 0);
        self.base_lbl = QLabel();
        grid.addWidget(self.base_lbl, 3, 1, Qt.AlignmentFlag.AlignRight)

        content_layout.addLayout(grid)
        self.svc_title = self.create_label("--- ADD-ONS ---", True, 10);
        content_layout.addWidget(self.svc_title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.svc_layout = QVBoxLayout();
        self.svc_layout.setContentsMargins(0, 0, 0, 0);
        content_layout.addLayout(self.svc_layout)

        content_layout.addStretch(1);
        scroll_area.setWidget(content_widget);
        container_layout.addWidget(scroll_area)

        final_total_widget = QWidget();
        final_total_layout = QGridLayout(final_total_widget)
        final_total_layout.addWidget(self.create_label("FINAL TOTAL:", True, 14), 0, 0)
        self.total_lbl = self.create_label("", True, 16);
        final_total_layout.addWidget(self.total_lbl, 0, 1, Qt.AlignmentFlag.AlignRight)
        container_layout.addWidget(final_total_widget)

        layout.addWidget(container)

        button = QPushButton("Start New Rental");
        button.clicked.connect(self.start_new_rental.emit);
        layout.addWidget(button)

    def update_receipt(self, name, data):
        self.name_lbl.setText(f"Client: {name}");
        self.car_lbl.setText(data["car"].name)
        self.dur_lbl.setText(f"{data['duration']} Day{'s' if data['duration'] > 1 else ''}");
        self.base_lbl.setText(format_peso(data["base_total"]))
        self.total_lbl.setText(format_peso(data["final_total"]))

        while self.svc_layout.count():
            item = self.svc_layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()
            elif layout := item.layout():
                while layout.count():
                    child = layout.takeAt(0)
                    if child_widget := child.widget(): child_widget.deleteLater()

        if data["services"]:
            self.svc_title.show()
            for svc in data["services"]:
                item = QHBoxLayout();
                item.addWidget(QLabel(f"- {svc['name']}"));
                item.addWidget(QLabel(format_peso(svc['cost'])), alignment=Qt.AlignmentFlag.AlignRight)
                self.svc_layout.addLayout(item)
        else:
            self.svc_title.hide()
            no_svc_label = QLabel("(No extra services selected)");
            no_svc_label.setStyleSheet("font-style: italic;")
            self.svc_layout.addWidget(no_svc_label, alignment=Qt.AlignmentFlag.AlignCenter)


# --- 4. Sidebar Widget ---

class SidebarWidget(QWidget):
    vehicle_list_requested = pyqtSignal()
    message_center_requested = pyqtSignal()
    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__();
        self.setFixedWidth(180)
        self.setObjectName("Sidebar")

        layout = QVBoxLayout(self);
        layout.setAlignment(Qt.AlignmentFlag.AlignTop);
        layout.setContentsMargins(0, 20, 0, 20)

        logo = QLabel("RAGADIO RENTALS");
        logo.setFont(QFont("Arial", 11, QFont.Weight.Bold));
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("margin-bottom:30px;");
        layout.addWidget(logo)

        cars_btn = QPushButton("Vehicle Options");
        cars_btn.clicked.connect(self.vehicle_list_requested.emit);
        layout.addWidget(cars_btn)
        message_btn = QPushButton("Send a Message");
        message_btn.clicked.connect(self.message_center_requested.emit);
        layout.addWidget(message_btn)

        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        logout_btn = QPushButton("Sign Out");
        logout_btn.clicked.connect(self.logout_requested.emit);
        layout.addWidget(logout_btn)


# --- 5. Admin Widgets ---

class SalesReportTab(BaseWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.txns, self.chart = [], None
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        search_group = QGroupBox("Search Transactions")
        search_layout = QHBoxLayout(search_group)
        search_layout.addWidget(QLabel("Search by Customer ID:"))
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Enter Customer ID...")
        self.search_bar.setValidator(QIntValidator(1, 9999999))
        search_layout.addWidget(self.search_bar)
        self.search_btn = QPushButton("Search")
        search_layout.addWidget(self.search_btn)
        self.reset_btn = QPushButton("Show All")
        search_layout.addWidget(self.reset_btn)
        layout.addWidget(search_group)

        total_revenue_layout = QHBoxLayout()
        total_revenue_layout.addWidget(self.create_label("Total Revenue Received:", True, 14))
        self.total_revenue_lbl = self.create_label("₱0.00", True, 14)
        self.total_revenue_lbl.setStyleSheet("color: #27ae60;")
        total_revenue_layout.addWidget(self.total_revenue_lbl, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(total_revenue_layout)

        self.chart_lbl = QLabel("Chart will be displayed here.");
        self.chart_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_lbl.setMinimumSize(400, 300);
        self.chart_lbl.setMaximumHeight(350)
        layout.addWidget(self.chart_lbl)

        layout.addWidget(self.create_label("--- Transaction List ---", True, 14),
                         alignment=Qt.AlignmentFlag.AlignCenter)

        self.table = QTableWidget();
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Date", "Customer ID", "Client", "Car", "Add-ons", "Days", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);
        layout.addWidget(self.table)

    def connect_signals(self):
        self.search_btn.clicked.connect(self.handle_search)
        self.reset_btn.clicked.connect(self.handle_reset)
        self.search_bar.returnPressed.connect(self.handle_search)

    def handle_search(self):
        user_id_str = self.search_bar.text().strip()
        if not user_id_str:
            QMessageBox.warning(self, "Empty Search", "Please enter a Customer ID.")
            return
        try:
            user_id = int(user_id_str)
            txns = self.manager.get_transactions_by_user_id(user_id)
            if not txns:
                QMessageBox.information(self, "No Results", f"No transactions found for Customer ID {user_id}.")
            self.populate_sales_report(txns)
        except ValueError:
            QMessageBox.warning(self, "Invalid ID", "Please enter a valid number for the Customer ID.")
        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"An error occurred: {e}")

    def handle_reset(self):
        self.search_bar.clear()
        all_txns = self.manager.get_all_transactions()
        self.populate_sales_report(all_txns)

    def generate_chart(self):
        try:
            df = pd.DataFrame([{'car_model': t.car.name, 'final_total': t.final_total} for t in self.txns])
            if df.empty: return None

            rental_counts = df.groupby('car_model').size().sort_values(ascending=False)
            colors = plt.cm.viridis(rental_counts.index.factorize()[0] / len(rental_counts))
            plt.figure(figsize=(10, 6), facecolor='#34495e')
            ax = plt.gca()
            ax.set_facecolor('#34495e')

            rental_counts.plot(kind='bar', color=colors)

            def count_formatter(x, pos):
                return f'{int(x)}'

            plt.gca().yaxis.set_major_formatter(FuncFormatter(count_formatter))

            text_color = '#ecf0f1'
            plt.title('Most Rented Units (Total Rental Count)', fontsize=16, weight='bold', color=text_color)
            plt.xlabel('Car Model', fontsize=12, color=text_color)
            plt.ylabel('Total Number of Rentals', fontsize=12, color=text_color)
            plt.xticks(rotation=45, ha='right', fontsize=10, color=text_color)
            plt.yticks(color=text_color)

            for spine in ax.spines.values():
                spine.set_color(text_color)
            ax.tick_params(axis='x', colors=text_color)
            ax.tick_params(axis='y', colors=text_color)

            plt.grid(axis='y', linestyle='--', alpha=0.7, color='#4a627c')
            plt.tight_layout()

            filename = 'sales_by_car_chart.png'
            plt.savefig(filename, facecolor=ax.get_facecolor());
            plt.close()
            return filename
        except Exception as e:
            print(f"Chart Error: {e}");
            return None

    def populate_sales_report(self, txns):
        self.txns = txns
        grand_total = sum(tx.final_total for tx in txns)
        self.total_revenue_lbl.setText(format_peso(grand_total))
        chart_file = self.generate_chart();
        self.chart = QPixmap(chart_file) if chart_file else None

        self.table.setRowCount(0)
        if not txns:
            self.table.setRowCount(1);
            item = QTableWidgetItem("No transactions recorded.");
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setSpan(0, 0, 1, 7);
            self.table.setItem(0, 0, item)
        else:
            self.table.setRowCount(len(txns))
            for row, tx in enumerate(txns):
                date = tx.timestamp.strftime("%Y-%m-%d %H:%M") if tx.timestamp else "N/A"
                total = QTableWidgetItem(format_peso(tx.final_total));
                total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                svcs = tx.services[0]['name'] if tx.services and tx.services[0]['name'] else "None"
                display_svcs = (svcs[:30] + '...') if len(svcs) > 33 else svcs

                self.table.setItem(row, 0, QTableWidgetItem(date));
                self.table.setItem(row, 1, QTableWidgetItem(str(tx.user.get('id', 'N/A'))))
                self.table.setItem(row, 2, QTableWidgetItem(tx.user.get('name', 'N/A')))
                self.table.setItem(row, 3, QTableWidgetItem(tx.car.name));
                self.table.setItem(row, 4, QTableWidgetItem(display_svcs))
                self.table.setItem(row, 5, QTableWidgetItem(str(tx.duration)));
                self.table.setItem(row, 6, total)

        self.table.resizeRowsToContents();
        self.table.resizeColumnsToContents();
        self.refresh_scaled_chart()

    def refresh_scaled_chart(self):
        if self.chart and not self.chart.isNull() and self.width() > 10:
            scaled = self.chart.scaled(self.chart_lbl.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
            self.chart_lbl.setPixmap(scaled)
        else:
            self.chart_lbl.setText("No chart data to display.")

    def resizeEvent(self, e):
        super().resizeEvent(e);
        self.refresh_scaled_chart()


class CarEditDialog(QDialog):
    def __init__(self, car_data, categories, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Car Details")

        self.layout = QFormLayout(self)

        self.name_in = QLineEdit(car_data['name'])
        self.price_in = QLineEdit(str(car_data['price_per_day']))
        self.price_in.setValidator(QDoubleValidator(0.00, 99999.99, 2))
        self.category_combo = QComboBox()

        current_index = 0
        for i, cat in enumerate(categories):
            self.category_combo.addItem(cat['name'], cat['id'])
            if cat['id'] == car_data['category_id']:
                current_index = i
        self.category_combo.setCurrentIndex(current_index)

        self.layout.addRow("Name:", self.name_in)
        self.layout.addRow("Price (₱):", self.price_in)
        self.layout.addRow("Category:", self.category_combo)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.buttons)

    def get_data(self):
        if not self.name_in.text().strip() or not self.price_in.text().strip():
            return None
        return {
            "name": self.name_in.text().strip(),
            "price": float(self.price_in.text()),
            "category_id": self.category_combo.currentData()
        }


class InventoryTab(BaseWidget):
    availability_updated = pyqtSignal()
    services_updated = pyqtSignal()

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.car_data = []
        self.all_categories = []
        self.all_services_data = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        nav_layout = QHBoxLayout()
        self.car_mgmt_btn = QPushButton("Manage Cars")
        self.service_mgmt_btn = QPushButton("Manage Add-ons")
        nav_layout.addWidget(self.car_mgmt_btn)
        nav_layout.addWidget(self.service_mgmt_btn)
        main_layout.addLayout(nav_layout)

        self.inventory_stack = QStackedWidget()
        main_layout.addWidget(self.inventory_stack)

        self.car_widget = QWidget()
        self.service_widget = QWidget()

        self.inventory_stack.addWidget(self.car_widget)
        self.inventory_stack.addWidget(self.service_widget)

        self.car_mgmt_btn.clicked.connect(lambda: self.inventory_stack.setCurrentWidget(self.car_widget))
        self.service_mgmt_btn.clicked.connect(self.go_to_services_page)

        self.setup_car_inventory_ui()
        self.setup_service_inventory_ui()

        self.populate_categories_dropdown()

    def go_to_services_page(self):
        self.populate_services_table()
        self.inventory_stack.setCurrentWidget(self.service_widget)

    def setup_car_inventory_ui(self):
        layout = QVBoxLayout(self.car_widget)
        layout.setSpacing(15)

        add_car_group = QGroupBox("Add New Car to Inventory")
        add_car_layout = QGridLayout(add_car_group)
        add_car_layout.addWidget(QLabel("Category:"), 0, 0)
        self.add_car_category_combo = QComboBox()
        add_car_layout.addWidget(self.add_car_category_combo, 0, 1)
        add_car_layout.addWidget(QLabel("Car Name:"), 1, 0)
        self.add_car_name_in = QLineEdit()
        self.add_car_name_in.setPlaceholderText("e.g., Toyota Fortuner")
        add_car_layout.addWidget(self.add_car_name_in, 1, 1)
        add_car_layout.addWidget(QLabel("Daily Rate (₱):"), 2, 0)
        self.add_car_price_in = QLineEdit()
        self.add_car_price_in.setPlaceholderText("e.g., 3500.00")
        self.add_car_price_in.setValidator(QDoubleValidator(0.00, 99999.99, 2))
        add_car_layout.addWidget(self.add_car_price_in, 2, 1)
        self.add_car_btn = QPushButton("Add Car to Fleet")
        self.add_car_btn.clicked.connect(self.handle_add_car)
        add_car_layout.addWidget(self.add_car_btn, 3, 0, 1, 2)
        layout.addWidget(add_car_group)

        layout.addWidget(self.create_label("Bulk Inventory Management", True, 14),
                         alignment=Qt.AlignmentFlag.AlignCenter)

        action_group = QGroupBox("Apply Status to Checked Cars");
        action_layout = QHBoxLayout(action_group)
        self.status_combo = QComboBox();
        self.status_combo.addItem("Set to: ✅ Available", 1)
        self.status_combo.addItem("Set to: ❌ Unavailable", 0)
        self.apply_bulk_btn = QPushButton("Apply to Selected");
        self.apply_bulk_btn.clicked.connect(self.apply_bulk_availability)
        action_layout.addWidget(self.status_combo);
        action_layout.addWidget(self.apply_bulk_btn);
        layout.addWidget(action_group)

        self.availability_table = QTableWidget();
        self.availability_table.setColumnCount(6)
        self.availability_table.setHorizontalHeaderLabels(
            ["Car Model", "Category", "Price", "Current Status", "Select", "Actions"])
        self.availability_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);
        layout.addWidget(self.availability_table)

        refresh_btn = QPushButton("Refresh List");
        refresh_btn.clicked.connect(self.populate_availability_table);
        layout.addWidget(refresh_btn)

    def setup_service_inventory_ui(self):
        layout = QVBoxLayout(self.service_widget)
        layout.setSpacing(15)

        add_service_group = QGroupBox("Add New Service / Add-on")
        add_service_layout = QGridLayout(add_service_group)

        add_service_layout.addWidget(QLabel("Service Name:"), 0, 0)
        self.add_service_name_in = QLineEdit()
        self.add_service_name_in.setPlaceholderText("e.g., Child Seat")
        add_service_layout.addWidget(self.add_service_name_in, 0, 1)

        add_service_layout.addWidget(QLabel("Price (₱):"), 1, 0)
        self.add_service_price_in = QLineEdit()
        self.add_service_price_in.setPlaceholderText("e.g., 500.00")
        self.add_service_price_in.setValidator(QDoubleValidator(0.00, 99999.99, 2))
        add_service_layout.addWidget(self.add_service_price_in, 1, 1)

        self.add_service_is_daily_check = QCheckBox("Charge is per day (not one-time)")
        add_service_layout.addWidget(self.add_service_is_daily_check, 2, 0, 1, 2)

        self.add_service_btn = QPushButton("Add Service")
        self.add_service_btn.clicked.connect(self.handle_add_service)
        add_service_layout.addWidget(self.add_service_btn, 3, 0, 1, 2)
        layout.addWidget(add_service_group)

        layout.addWidget(self.create_label("Current Services", True, 14), alignment=Qt.AlignmentFlag.AlignCenter)

        self.service_table = QTableWidget()
        self.service_table.setColumnCount(5)
        self.service_table.setHorizontalHeaderLabels(["ID", "Name", "Price", "Charge Type", "Actions"])
        self.service_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.service_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.service_table)

        refresh_btn = QPushButton("Refresh Service List")
        refresh_btn.clicked.connect(self.populate_services_table)
        layout.addWidget(refresh_btn)

    def populate_categories_dropdown(self):
        self.add_car_category_combo.clear()
        try:
            self.all_categories = self.manager.get_categories()
            if not self.all_categories:
                self.add_car_category_combo.addItem("Error: No categories found", "")
                return
            for cat in self.all_categories:
                self.add_car_category_combo.addItem(cat['name'], cat['id'])
        except Exception as e:
            print(f"Failed to populate categories: {e}")
            self.add_car_category_combo.addItem("Error loading...", "")

    def handle_add_car(self):
        category_id = self.add_car_category_combo.currentData()
        car_name = self.add_car_name_in.text().strip()
        price_str = self.add_car_price_in.text().strip()

        if not all([category_id, car_name, price_str]):
            QMessageBox.warning(self, "Missing Information", "Please fill in all fields (Category, Name, and Price).")
            return
        try:
            price_val = float(price_str)
            if price_val <= 0:
                raise ValueError("Price must be positive")
        except ValueError:
            QMessageBox.warning(self, "Invalid Price", "Please enter a valid price (e.g., 3500.00).")
            return

        try:
            result = self.manager.add_new_car(category_id, car_name, price_val)
            if result is True:
                QMessageBox.information(self, "Success", f"'{car_name}' has been added to the inventory.")
                self.add_car_name_in.clear()
                self.add_car_price_in.clear()
                self.populate_availability_table()
                self.availability_updated.emit()
            else:
                QMessageBox.critical(self, "Failed to Add Car", f"Error: {result}")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An unexpected error occurred: {e}")

    def populate_availability_table(self):
        self.car_data = self.manager.get_all_cars_for_admin();
        self.availability_table.setRowCount(len(self.car_data))

        for i in range(self.availability_table.columnCount()):
            self.availability_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        for row, car in enumerate(self.car_data):
            self.availability_table.setItem(row, 0, QTableWidgetItem(car['name']))
            self.availability_table.setItem(row, 1, QTableWidgetItem(car['category_name']))

            price_item = QTableWidgetItem(format_peso(car['price_per_day']));
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.availability_table.setItem(row, 2, price_item)

            status_text = "✅ Available" if bool(car['is_available']) else "❌ Unavailable";
            status_item = QTableWidgetItem(status_text)
            self.availability_table.setItem(row, 3, status_item)

            checkbox = QCheckBox();
            checkbox.setCheckState(Qt.CheckState.Unchecked)
            checkbox.setProperty("car_id", car['id'])
            widget_wrapper = QWidget();
            cb_layout = QHBoxLayout(widget_wrapper)
            cb_layout.addWidget(checkbox);
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter);
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self.availability_table.setCellWidget(row, 4, widget_wrapper)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda _, r=row: self.handle_edit_car(r))
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("SecondaryButton")
            delete_btn.clicked.connect(lambda _, r=row: self.handle_delete_car(r))

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            self.availability_table.setCellWidget(row, 5, actions_widget)

        self.availability_table.resizeColumnsToContents()
        self.availability_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.availability_table.resizeRowsToContents()

    def handle_edit_car(self, row):
        car_to_edit = self.car_data[row]
        dialog = CarEditDialog(car_to_edit, self.all_categories, self)
        if dialog.exec():
            new_data = dialog.get_data()
            if not new_data:
                QMessageBox.warning(self, "Invalid Data", "All fields must be filled correctly.")
                return

            result = self.manager.edit_car(
                car_to_edit['id'],
                new_data['name'],
                new_data['price'],
                new_data['category_id']
            )

            if result is True:
                QMessageBox.information(self, "Success", f"'{new_data['name']}' was updated.")
                self.populate_availability_table()
                self.availability_updated.emit()
            else:
                QMessageBox.critical(self, "Update Failed", f"Error: {result}")

    def handle_delete_car(self, row):
        car_to_delete = self.car_data[row]
        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to permanently delete '{car_to_delete['name']}'?\n\nThis cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Yes:
            result = self.manager.delete_car(car_to_delete['id'])
            if result is True:
                QMessageBox.information(self, "Success", f"'{car_to_delete['name']}' was deleted.")
                self.populate_availability_table()
                self.availability_updated.emit()
            else:
                QMessageBox.critical(self, "Delete Failed", f"Error: {result}")

    def apply_bulk_availability(self):
        new_status = self.status_combo.currentData();
        selected_car_ids = []
        for row in range(self.availability_table.rowCount()):
            widget_wrapper = self.availability_table.cellWidget(row, 4)
            if widget_wrapper:
                checkbox = widget_wrapper.findChild(QCheckBox)
                if checkbox and checkbox.isChecked(): selected_car_ids.append(checkbox.property("car_id"))

        if not selected_car_ids:
            QMessageBox.warning(self, "No Selection", "Please select at least one car to update.");
            return

        success_count = 0
        try:
            for car_id in selected_car_ids:
                self.manager.update_car_unit_availability(car_id, new_status);
                success_count += 1
            QMessageBox.information(self, "Update Complete",
                                    f"Successfully set {success_count} car(s) to {'Available' if new_status else 'Unavailable'}.")
            self.populate_availability_table();
            self.availability_updated.emit()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update availability: {e}")

    def handle_add_service(self):
        name = self.add_service_name_in.text().strip()
        price_str = self.add_service_price_in.text().strip()
        is_daily = self.add_service_is_daily_check.isChecked()

        if not name or not price_str:
            QMessageBox.warning(self, "Missing Information", "Please fill in both Name and Price.")
            return

        try:
            price = float(price_str)
            if price < 0: raise ValueError("Price cannot be negative")
        except ValueError:
            QMessageBox.warning(self, "Invalid Price", "Please enter a valid price (e.g., 500.00).")
            return

        result = self.manager.add_new_service(name, price, is_daily)

        if result is True:
            QMessageBox.information(self, "Success", f"Service '{name}' added.")
            self.add_service_name_in.clear()
            self.add_service_price_in.clear()
            self.add_service_is_daily_check.setChecked(False)
            self.populate_services_table()
            self.services_updated.emit()
        else:
            QMessageBox.critical(self, "Failed to Add", f"Error: {result}")

    def populate_services_table(self):
        self.all_services_data = self.manager.get_all_services_with_ids()
        self.service_table.setRowCount(len(self.all_services_data))

        for row, service in enumerate(self.all_services_data):
            self.service_table.setItem(row, 0, QTableWidgetItem(str(service['id'])))
            self.service_table.setItem(row, 1, QTableWidgetItem(service['name']))

            price_item = QTableWidgetItem(format_peso(service['price']))
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.service_table.setItem(row, 2, price_item)

            type_text = "Per Day" if bool(service['is_daily']) else "One-Time"
            self.service_table.setItem(row, 3, QTableWidgetItem(type_text))

            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("SecondaryButton")
            delete_btn.clicked.connect(lambda _, r=row: self.handle_delete_service(r))
            self.service_table.setCellWidget(row, 4, delete_btn)

        self.service_table.resizeColumnsToContents()
        self.service_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def handle_delete_service(self, row):
        service_to_delete = self.all_services_data[row]

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete the service '{service_to_delete['name']}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Yes:
            result = self.manager.delete_service(service_to_delete['id'])
            if result is True:
                QMessageBox.information(self, "Success", f"'{service_to_delete['name']}' was deleted.")
                self.populate_services_table()
                self.services_updated.emit()
            else:
                QMessageBox.critical(self, "Delete Failed", f"Error: {result}")


class MessagesTab(BaseWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.create_label("Customer Messages", True, 14), alignment=Qt.AlignmentFlag.AlignCenter)

        self.message_table = QTableWidget();
        self.message_table.setColumnCount(4)
        self.message_table.setHorizontalHeaderLabels(["Date", "Name", "Email", "Message Snippet"])
        self.message_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.message_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.message_table.itemDoubleClicked.connect(self.show_full_message);
        layout.addWidget(self.message_table)

        refresh_btn = QPushButton("Refresh Messages");
        refresh_btn.clicked.connect(self.populate_message_table);
        layout.addWidget(refresh_btn)

    def populate_message_table(self):
        messages = self.manager.get_all_messages();
        self.message_table.setRowCount(len(messages))

        for row, msg in enumerate(messages):
            try:
                date_obj = datetime.datetime.fromisoformat(msg['timestamp'])
                date_str = date_obj.strftime("%Y-%m-%d %H:%M")
            except (TypeError, ValueError):
                date_str = "N/A"

            snippet = msg['message_text'][:50].replace('\n', ' ') + '...' if len(msg['message_text']) > 50 else msg[
                'message_text']

            self.message_table.setItem(row, 0, QTableWidgetItem(date_str));
            self.message_table.setItem(row, 1, QTableWidgetItem(msg['user_name']))
            self.message_table.setItem(row, 2, QTableWidgetItem(msg['user_email']))

            snippet_item = QTableWidgetItem(snippet);
            snippet_item.setData(Qt.ItemDataRole.UserRole, msg['message_text'])
            self.message_table.setItem(row, 3, snippet_item)

        self.message_table.resizeRowsToContents();
        self.message_table.resizeColumnsToContents()

    def show_full_message(self, item):
        if item.column() == 3:
            full_message = item.data(Qt.ItemDataRole.UserRole)
            user_row = self.message_table.row(item)
            name = self.message_table.item(user_row, 1).text();
            email = self.message_table.item(user_row, 2).text()
            QMessageBox.information(self, f"Message from {name}", f"From: {email}\n\n{full_message}")


class AdminDashboardWidget(BaseWidget):
    availability_updated = pyqtSignal()
    services_updated = pyqtSignal()
    signout_requested = pyqtSignal()

    def __init__(self, rental_manager):
        super().__init__();
        self.manager = rental_manager

        main_layout = QVBoxLayout(self);
        main_layout.setSpacing(10)

        dashboard_title = self.create_label("Administrator Dashboard", True, 18)
        dashboard_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(dashboard_title)

        self.stacked_sections = QStackedWidget()
        self.sales_tab = SalesReportTab(self.manager)
        self.inventory_tab = InventoryTab(self.manager)
        self.messages_tab = MessagesTab(self.manager)

        self.stacked_sections.addWidget(self.sales_tab);
        self.stacked_sections.addWidget(self.inventory_tab)
        self.stacked_sections.addWidget(self.messages_tab)

        nav_layout = QHBoxLayout()
        self.sales_btn = QPushButton("📈 Sales Report");
        self.availability_btn = QPushButton("🛠️ Inventory (Cars/Services)")
        self.messages_btn = QPushButton("💬 Customer Messages")

        self.sales_btn.clicked.connect(self._go_to_sales)
        self.availability_btn.clicked.connect(self._go_to_inventory)
        self.messages_btn.clicked.connect(self._go_to_messages)

        nav_layout.addWidget(self.sales_btn);
        nav_layout.addWidget(self.availability_btn);
        nav_layout.addWidget(self.messages_btn)
        main_layout.addLayout(nav_layout);
        main_layout.addWidget(self.stacked_sections)

        bottom_buttons_layout = QHBoxLayout()
        signout_btn = QPushButton("🚪 Admin Sign Out")
        signout_btn.setObjectName("DangerButton")
        signout_btn.clicked.connect(self.signout_requested.emit)

        bottom_buttons_layout.addStretch(1)
        bottom_buttons_layout.addWidget(signout_btn)
        bottom_buttons_layout.addStretch(1)

        main_layout.addLayout(bottom_buttons_layout)

        self.inventory_tab.availability_updated.connect(self.availability_updated.emit)
        self.inventory_tab.services_updated.connect(self.services_updated.emit)

    def _go_to_sales(self):
        self.sales_tab.handle_reset()
        self.stacked_sections.setCurrentWidget(self.sales_tab)

    def _go_to_inventory(self):
        self.inventory_tab.populate_categories_dropdown()
        self.inventory_tab.populate_availability_table();
        self.inventory_tab.populate_services_table();
        self.stacked_sections.setCurrentWidget(self.inventory_tab)

    def _go_to_messages(self):
        self.messages_tab.populate_message_table()
        self.stacked_sections.setCurrentWidget(self.messages_tab)
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import datetime
import mysql.connector
import hashlib
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget,
    QGridLayout, QMessageBox, QGroupBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
    QScrollArea, QTextEdit, QSpacerItem, QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIntValidator, QPixmap, QIcon, QDoubleValidator
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


# --- Utility Functions ---

def hash_password(password):
    """Hashes the password using SHA256 for secure storage."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def format_peso(amount):
    return f"₱{amount:,.2f}"


# --- Database Manager ---

class DBManager:
    def __init__(self, host="localhost", user="root", password="", database="car_rental_db_final"):
        self.host, self.user, self.password, self.database = host, user, password, database
        self.conn, self.cursor = None, None
        self.connect()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(host=self.host, user=self.user, password=self.password)
            self.cursor = self.conn.cursor()
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            self.conn.close()
            self.conn = mysql.connector.connect(host=self.host, user=self.user, password=self.password,
                                                database=self.database)
            self.cursor = self.conn.cursor(dictionary=True)
            self._create_tables()
            self._insert_initial_data()
        except mysql.connector.Error as err:
            QMessageBox.critical(None, "Database Error",
                                 f"Failed to connect to MySQL: {err}.\nPlease ensure your database server (like XAMPP) is running.")
            sys.exit(1)

    def _create_tables(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS categories (id VARCHAR(10) PRIMARY KEY, name VARCHAR(100) NOT NULL)")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id INT AUTO_INCREMENT PRIMARY KEY, category_id VARCHAR(10), 
                name VARCHAR(100) NOT NULL UNIQUE, price_per_day DECIMAL(10, 2) NOT NULL,
                is_available BOOLEAN DEFAULT TRUE, FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE, password_hash VARCHAR(256) NOT NULL
            )
        """)

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS services (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL UNIQUE, price DECIMAL(10, 2) NOT NULL, is_daily BOOLEAN NOT NULL)")

        # --- MODIFIED: Added user_id column ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY, 
                user_id INT, 
                timestamp DATETIME, 
                user_name VARCHAR(100), 
                user_email VARCHAR(100), 
                car_model VARCHAR(100), 
                duration INT, 
                services_used TEXT, 
                final_total DECIMAL(10, 2)
            )
        """)

        # --- NEW: Safely add user_id column and foreign key if they don't exist ---
        try:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN user_id INT")
        except mysql.connector.Error as err:
            if err.errno == 1060:
                pass  # Duplicate column
            else:
                print(f"DB Warning: {err}")
        try:
            self.cursor.execute(
                "ALTER TABLE transactions ADD CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(id)")
        except mysql.connector.Error as err:
            if err.errno == 1826 or err.errno == 1022:
                pass  # Constraint already exists
            else:
                print(f"DB Warning: {err}")
        # --- END NEW ---

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY, timestamp DATETIME, user_name VARCHAR(100),
                user_email VARCHAR(100), message_text TEXT
            )
        """)
        self.conn.commit()

    def _insert_initial_data(self):
        categories = [('1', '6 Seaters (SUVs, MPVs, Vans)'), ('2', '4 Seaters (Sedans & Specialty)')]
        self.cursor.executemany("INSERT IGNORE INTO categories (id, name) VALUES (%s, %s)", categories)

        cars = [('1', 'Toyota Innova (MPV)', 3200.00), ('1', 'Mitsubishi Xpander (MPV)', 2800.00),
                ('1', 'Nissan Terra (SUV)', 4500.00), ('1', 'Ford Everest (SUV)', 4300.00),
                ('1', 'Hyundai Staria (Van)', 6000.00), ('2', 'Toyota Vios / Honda City', 1750.00),
                ('2', 'Mazda 3', 2200.00), ('2', 'Honda Civic Turbo', 2600.00),
                ('2', 'Toyota Camry', 3500.00), ('2', 'BMW 3-Series (Luxury)', 5000.00)]
        car_names = [c[1] for c in cars]
        self.cursor.execute(f"SELECT name FROM cars WHERE name IN ({', '.join(['%s'] * len(car_names))})", car_names)
        existing_cars = {row['name'] for row in self.cursor.fetchall()}
        new_cars = [c for c in cars if c[1] not in existing_cars]
        if new_cars:
            self.cursor.executemany("INSERT INTO cars (category_id, name, price_per_day) VALUES (%s, %s, %s)", new_cars)

        self.cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'test@user.com'")
        if self.cursor.fetchone()['COUNT(*)'] == 0:
            self.cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                                ("Test User", "test@user.com", hash_password("password")))

        services = [('Insurance and Waivers', 1500.00, False), ('RFID Pass (Toll Fees)', 750.00, False)]
        service_names = [s[0] for s in services]
        self.cursor.execute(f"SELECT name FROM services WHERE name IN ({', '.join(['%s'] * len(service_names))})",
                            service_names)
        existing_services = {row['name'] for row in self.cursor.fetchall()}
        new_services = [s for s in services if s[0] not in existing_services]
        if new_services:
            self.cursor.executemany("INSERT INTO services (name, price, is_daily) VALUES (%s, %s, %s)", new_services)

        self.conn.commit()

    def register_user(self, name, email, password_hash):
        try:
            self.cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                                (name, email, password_hash))
            self.conn.commit()
            return True
        except mysql.connector.Error as err:
            if err.errno == 1062: return "Email already registered."
            return str(err)

    def login_user(self, email, password_hash):
        # --- MODIFIED: Select id as well ---
        self.cursor.execute("SELECT id, name, email FROM users WHERE email = %s AND password_hash = %s",
                            (email, password_hash))
        return self.cursor.fetchone()

    def get_all_cars_data(self, only_available=False):
        query = "SELECT id, name, price_per_day, is_available FROM cars"
        if only_available: query += " WHERE is_available = TRUE"
        self.cursor.execute(query + " ORDER BY category_id, name")
        return self.cursor.fetchall()

    def get_cars_by_category(self, category_id, only_available=False):
        query = "SELECT name, price_per_day, is_available FROM cars WHERE category_id = %s"
        if only_available: query += " AND is_available = TRUE"
        self.cursor.execute(query, (category_id,))
        return [Car(c['name'], c['price_per_day'], c['is_available']) for c in self.cursor.fetchall()]

    def update_car_availability(self, car_id, is_available):
        self.cursor.execute("UPDATE cars SET is_available = %s WHERE id = %s", (is_available, car_id))
        self.conn.commit()

    def get_all_categories(self):
        self.cursor.execute("SELECT id, name FROM categories ORDER BY id")
        return self.cursor.fetchall()

    def add_car(self, category_id, name, price):
        """Adds a new car to the database."""
        try:
            self.cursor.execute(
                "INSERT INTO cars (category_id, name, price_per_day, is_available) VALUES (%s, %s, %s, %s)",
                (category_id, name, price, True)  # Default to available
            )
            self.conn.commit()
            return True
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry
                return f"A car with the name '{name}' already exists."
            return str(err)

    def get_all_services(self):
        self.cursor.execute("SELECT name, price, is_daily FROM services")
        return self.cursor.fetchall()

    def save_transaction(self, txn):
        services = ", ".join([f"{s['name']} (₱{s['cost']:,.2f})" for s in txn.services])
        # --- MODIFIED: Add user_id to data tuple ---
        data = (txn.user.get('id'), txn.timestamp, txn.user.get('name'), txn.user.get('email'),
                txn.car.name, txn.duration, services, txn.final_total)

        # --- MODIFIED: Add user_id to INSERT statement ---
        self.cursor.execute(
            "INSERT INTO transactions (user_id, timestamp, user_name, user_email, car_model, duration, services_used, final_total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            data)
        self.conn.commit()

    def save_message(self, name, email, message):
        self.cursor.execute(
            "INSERT INTO messages (timestamp, user_name, user_email, message_text) VALUES (%s, %s, %s, %s)",
            (datetime.datetime.now(), name, email, message))
        self.conn.commit()

    # --- PRIVATE HELPER to build transaction objects ---
    def _build_transactions_from_rows(self, rows):
        transactions = []
        for raw in rows:
            dummy_car = Car(raw['car_model'], 0)
            # --- MODIFIED: Add user_id to user_data dict ---
            user_data = {
                "id": raw.get('user_id'),
                "name": raw['user_name'],
                "email": raw['user_email']
            }
            services_text = raw.get('services_used', '')
            services = [{"name": services_text, "cost": 0}] if services_text else []
            txn = Transaction(user=user_data, car=dummy_car, duration=raw.get('duration', 0), services=services,
                              final_total=raw.get('final_total', 0.0))
            txn.timestamp = raw.get('timestamp')
            transactions.append(txn)
        return transactions

    def get_all_transactions(self):
        self.cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
        return self._build_transactions_from_rows(self.cursor.fetchall())

    # --- NEW: Get transactions for a specific user ---
    def get_transactions_by_user_id(self, user_id):
        self.cursor.execute("SELECT * FROM transactions WHERE user_id = %s ORDER BY timestamp DESC", (user_id,))
        return self._build_transactions_from_rows(self.cursor.fetchall())

    # --- END NEW ---

    def get_all_messages(self):
        self.cursor.execute("SELECT * FROM messages ORDER BY timestamp DESC")
        return self.cursor.fetchall()

    def close(self):
        if self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()


# --- Data Classes & System ---

class Car:
    def __init__(self, name, price_per_day, is_available=True):
        self._name, self._price, self._is_available = name, price_per_day, is_available

    @property
    def name(self): return self._name

    @property
    def price_per_day(self): return self._price

    @property
    def is_available(self): return self._is_available

    def to_string(self):
        status = " (Available)" if self._is_available else " (UNAVAILABLE)"
        return f"{self._name} - {format_peso(self._price)} / day{status}"


class Transaction:
    def __init__(self, user, car, duration, services, final_total):
        self.timestamp = datetime.datetime.now()
        # user is now a dict: {'id': 1, 'name': 'Test', 'email': '...'}
        self.user, self.car, self.duration, self.services, self.final_total = user, car, duration, services, final_total


class RentalManager:
    def __init__(self, db_manager):
        self.db = db_manager
        # --- MODIFIED: current_user will now hold 'id' as well ---
        self.current_user = {"id": None, "name": "", "email": ""}

    # --- Merged from RentalSystem ---
    def get_categories(self): return self.db.get_all_categories()

    def get_cars(self, cat_id): return self.db.get_cars_by_category(cat_id, only_available=True)

    def get_services(self): return [{"name": s['name'], "price": s['price'], "is_daily": bool(s['is_daily'])} for s in
                                    self.db.get_all_services()]

    # --- End Merged ---

    def register(self, name, email, password):
        return self.db.register_user(name, email, hash_password(password))

    def login(self, email, password):
        user_data = self.db.login_user(email, hash_password(password))
        if user_data:
            # --- MODIFIED: Store 'id' in current_user ---
            self.current_user = {"id": user_data['id'], "name": user_data['name'], "email": user_data['email']}
            return True
        return False

    def logout(self):
        # --- MODIFIED: Reset 'id' on logout ---
        self.current_user = {"id": None, "name": "", "email": ""}

    def record_transaction(self, data):
        # No change needed here, self.current_user already has the 'id'
        txn = Transaction(user=self.current_user, car=data["car"], duration=data["duration"], services=data["services"],
                          final_total=data["final_total"])
        self.db.save_transaction(txn)

    def save_message(self, name, email, message):
        self.db.save_message(name, email, message)

    def get_all_cars_for_admin(self): return self.db.get_all_cars_data(only_available=False)

    def add_new_car(self, category_id, name, price):
        """Wrapper for adding a new car."""
        return self.db.add_car(category_id, name, price)

    def update_car_unit_availability(self, car_id, is_available):
        self.db.update_car_availability(car_id, is_available)

    def get_all_transactions(self): return self.db.get_all_transactions()

    # --- NEW: Pass-through method for searching transactions ---
    def get_transactions_by_user_id(self, user_id):
        return self.db.get_transactions_by_user_id(user_id)

    # --- END NEW ---

    def get_all_messages(self): return self.db.get_all_messages()


# --- GUI Widgets ---

class BaseWidget(QWidget):
    def __init__(self): super().__init__()

    def create_label(self, text, bold=False, size=12):
        lbl = QLabel(text)
        if bold: lbl.setFont(QFont("Arial", size, QFont.Weight.Bold))
        return lbl


# --- Login and Signup Widgets ---

class LoginWidget(BaseWidget):
    customer_login_successful = pyqtSignal(str, str)  # Renamed from login_successful
    register_requested = pyqtSignal()
    admin_login_successful = pyqtSignal()  # Renamed from admin_requested

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
        self.email_in.setMinimumWidth(300)  # Give it a decent size
        self.password_in = QLineEdit();
        self.password_in.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_in.setPlaceholderText("Password");
        self.password_in.setMinimumWidth(300)
        self.password_in.returnPressed.connect(self.handle_login)

        login_btn = QPushButton("Log In");
        login_btn.clicked.connect(self.handle_login)

        links_layout = QHBoxLayout()
        links_layout.setContentsMargins(50, 0, 50, 0)
        signup_lbl = QLabel("<a href='#'>Don't have an account? Sign Up</a>");
        signup_lbl.linkActivated.connect(self.register_requested.emit)

        links_layout.addWidget(signup_lbl, alignment=Qt.AlignmentFlag.AlignLeft)

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
        layout.addLayout(links_layout)

    def handle_login(self):
        email, password = self.email_in.text().strip(), self.password_in.text()
        if not (email and password):
            QMessageBox.warning(self, "Error", "Please enter both email and password.")
            return

        # 1. Check for Admin credentials first
        if email.lower() == "admin@gmail.com" and password == "admin123":
            self.admin_login_successful.emit()
            self.email_in.clear()
            self.password_in.clear()

        # 2. If not admin, check for Customer
        elif self.manager.login(email, password):
            # Login now populates self.manager.current_user with 'id'
            self.customer_login_successful.emit(self.manager.current_user['name'], email)
            self.email_in.clear()
            self.password_in.clear()

        # 3. If neither, login failed
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
        try:
            pixmap = QPixmap("car-removebg-preview.png").scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio,
                                                                Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap)
        except:
            logo.setText("🚗");
            logo.setFont(QFont("Arial", 48))
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
        self.signup_w.email_in.clear()
        self.signup_w.password_in.clear();
        self.signup_w.confirm_password_in.clear()


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

        addons_group = QGroupBox("Add-ons");
        addons_layout = QVBoxLayout();
        addons_group.setLayout(addons_layout)
        for svc in self.manager.get_services():
            price_text = f"{format_peso(svc['price'])} / day" if svc['is_daily'] else format_peso(svc['price'])
            box = QCheckBox(f"{svc['name']} ({price_text})");
            box.setProperty("svc_data", svc)
            addons_layout.addWidget(box);
            self.svc_boxes.append(box)

        options_layout_container.addWidget(options_group);
        options_layout_container.addWidget(addons_group)
        options_layout_container.addStretch(1);
        scroll.setWidget(content_widget);
        main_layout.addWidget(scroll)

        confirm_btn = QPushButton("Confirm Booking");
        confirm_btn.clicked.connect(self.confirm_and_book);
        main_layout.addWidget(confirm_btn)
        back_btn = QPushButton("← Back to Car Selection");
        back_btn.clicked.connect(self.back_to_vehicles.emit);
        main_layout.addWidget(back_btn)

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
                cost = svc['price'] * days if svc['is_daily'] else svc['price']
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
        try:
            pixmap = QPixmap("car-removebg-preview.png").scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio,
                                                                Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap)
        except:
            logo.setText("🚗");
            logo.setFont(QFont("Arial", 20))
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


# --- REFACTORED ADMIN WIDGETS ---

class SalesReportTab(BaseWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.txns, self.chart = [], None
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- NEW: Search Bar ---
        search_group = QGroupBox("Search Transactions")
        search_layout = QHBoxLayout(search_group)
        search_layout.addWidget(QLabel("Search by Customer ID:"))
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Enter Customer ID...")
        self.search_bar.setValidator(QIntValidator(1, 9999999))  # Only allow numbers
        search_layout.addWidget(self.search_bar)
        self.search_btn = QPushButton("Search")
        search_layout.addWidget(self.search_btn)
        self.reset_btn = QPushButton("Show All")
        search_layout.addWidget(self.reset_btn)
        layout.addWidget(search_group)
        # --- END NEW ---

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
        # --- MODIFIED: Added Customer ID column (7 total) ---
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Date", "Customer ID", "Client", "Car", "Add-ons", "Days", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Stretch Client name
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);
        layout.addWidget(self.table)

    # --- NEW: Connect search buttons ---
    def connect_signals(self):
        self.search_btn.clicked.connect(self.handle_search)
        self.reset_btn.clicked.connect(self.handle_reset)
        self.search_bar.returnPressed.connect(self.handle_search)

    # --- NEW: Search logic ---
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

            # Re-use the existing populate method with the filtered list
            self.populate_sales_report(txns)
        except ValueError:
            QMessageBox.warning(self, "Invalid ID", "Please enter a valid number for the Customer ID.")
        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"An error occurred: {e}")

    # --- NEW: Reset logic ---
    def handle_reset(self):
        self.search_bar.clear()
        all_txns = self.manager.get_all_transactions()
        self.populate_sales_report(all_txns)

    # --- END NEW ---

    def generate_chart(self):
        try:
            # Use self.txns (which is the *currently displayed* list)
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
        # This list is now either ALL transactions or a FILTERED list
        self.txns = txns

        # Calculate revenue based on the *displayed* transactions
        grand_total = sum(tx.final_total for tx in txns)
        self.total_revenue_lbl.setText(format_peso(grand_total))

        # Generate chart based on the *displayed* transactions
        chart_file = self.generate_chart();
        self.chart = QPixmap(chart_file) if chart_file else None

        self.table.setRowCount(0)
        if not txns:
            self.table.setRowCount(1);
            item = QTableWidgetItem("No transactions recorded.");
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # --- MODIFIED: Span 7 columns ---
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

                # --- MODIFIED: Add Customer ID and shift other columns ---
                self.table.setItem(row, 0, QTableWidgetItem(date));
                self.table.setItem(row, 1, QTableWidgetItem(str(tx.user.get('id', 'N/A'))))  # NEW
                self.table.setItem(row, 2, QTableWidgetItem(tx.user.get('name', 'N/A')))
                self.table.setItem(row, 3, QTableWidgetItem(tx.car.name));
                self.table.setItem(row, 4, QTableWidgetItem(display_svcs))
                self.table.setItem(row, 5, QTableWidgetItem(str(tx.duration)));
                self.table.setItem(row, 6, total)
                # --- END MODIFIED ---

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


class InventoryTab(BaseWidget):
    availability_updated = pyqtSignal()

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.car_data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
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
        self.status_combo.addItem("Set to: ✅ Available", True)
        self.status_combo.addItem("Set to: ❌ Unavailable", False)
        self.apply_bulk_btn = QPushButton("Apply to Selected");
        self.apply_bulk_btn.clicked.connect(self.apply_bulk_availability)
        action_layout.addWidget(self.status_combo);
        action_layout.addWidget(self.apply_bulk_btn);
        layout.addWidget(action_group)

        self.availability_table = QTableWidget();
        self.availability_table.setColumnCount(4)
        self.availability_table.setHorizontalHeaderLabels(["Car Model", "Price", "Current Status", "Select"])
        self.availability_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);
        layout.addWidget(self.availability_table)

        refresh_btn = QPushButton("Refresh List");
        refresh_btn.clicked.connect(self.populate_availability_table);
        layout.addWidget(refresh_btn)

        self.populate_categories_dropdown()

    def populate_categories_dropdown(self):
        self.add_car_category_combo.clear()
        try:
            categories = self.manager.get_categories()
            if not categories:
                self.add_car_category_combo.addItem("Error: No categories found", "")
                return
            for cat in categories:
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
            price_item = QTableWidgetItem(format_peso(car['price_per_day']));
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.availability_table.setItem(row, 1, price_item)
            status_text = "✅ Available" if car['is_available'] else "❌ Unavailable";
            status_item = QTableWidgetItem(status_text)
            self.availability_table.setItem(row, 2, status_item)
            checkbox = QCheckBox();
            checkbox.setCheckState(Qt.CheckState.Unchecked)
            checkbox.setProperty("car_id", car['id'])
            widget_wrapper = QWidget();
            cb_layout = QHBoxLayout(widget_wrapper)
            cb_layout.addWidget(checkbox);
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter);
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self.availability_table.setCellWidget(row, 3, widget_wrapper)

        self.availability_table.resizeColumnsToContents()
        self.availability_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.availability_table.resizeRowsToContents()

    def apply_bulk_availability(self):
        new_status = self.status_combo.currentData();
        selected_car_ids = []
        for row in range(self.availability_table.rowCount()):
            widget_wrapper = self.availability_table.cellWidget(row, 3)
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
            date = msg['timestamp'].strftime("%Y-%m-%d %H:%M") if msg['timestamp'] else "N/A"
            snippet = msg['message_text'][:50].replace('\n', ' ') + '...' if len(msg['message_text']) > 50 else msg[
                'message_text']

            self.message_table.setItem(row, 0, QTableWidgetItem(date));
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
    # --- MODIFIED: Removed back_to_main signal ---
    availability_updated = pyqtSignal()
    signout_requested = pyqtSignal()

    # --- END MODIFIED ---

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
        self.availability_btn = QPushButton("🛠️ Inventory Availability")
        self.messages_btn = QPushButton("💬 Customer Messages")

        self.sales_btn.clicked.connect(self._go_to_sales)  # Modified
        self.availability_btn.clicked.connect(self._go_to_inventory)
        self.messages_btn.clicked.connect(self._go_to_messages)

        nav_layout.addWidget(self.sales_btn);
        nav_layout.addWidget(self.availability_btn);
        nav_layout.addWidget(self.messages_btn)
        main_layout.addLayout(nav_layout);
        main_layout.addWidget(self.stacked_sections)

        # --- MODIFIED: Removed the "Back to Rentals" button ---
        bottom_buttons_layout = QHBoxLayout()
        signout_btn = QPushButton("🚪 Admin Sign Out")
        signout_btn.setObjectName("DangerButton")
        signout_btn.clicked.connect(self.signout_requested.emit)

        # Center the signout button
        bottom_buttons_layout.addStretch(1)
        bottom_buttons_layout.addWidget(signout_btn)
        bottom_buttons_layout.addStretch(1)

        main_layout.addLayout(bottom_buttons_layout)
        # --- END MODIFIED ---

        # Proxy the signal from the inventory tab
        self.inventory_tab.availability_updated.connect(self.availability_updated.emit)

    # --- NEW: Go to sales (resets search) ---
    def _go_to_sales(self):
        # Use the reset method to clear search and load all
        self.sales_tab.handle_reset()
        self.stacked_sections.setCurrentWidget(self.sales_tab)

    def _go_to_inventory(self):
        self.inventory_tab.populate_categories_dropdown()
        self.inventory_tab.populate_availability_table();
        self.stacked_sections.setCurrentWidget(self.inventory_tab)

    def _go_to_messages(self):
        self.messages_tab.populate_message_table()
        self.stacked_sections.setCurrentWidget(self.messages_tab)


# --- END REFACTORED ADMIN WIDGETS ---


class SidebarWidget(QWidget):
    vehicle_list_requested = pyqtSignal()
    admin_access_requested = pyqtSignal()
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


# --- Main Application ---
class RentalApp(QMainWindow):
    def __init__(self):
        super().__init__();
        self.setWindowTitle("Ragadio's Car Rentals")
        try:
            self.setWindowIcon(QIcon("car-removebg-preview.png"))
        except:
            pass

        # --- SIZES (Standardized) ---
        self.vehicle_list_size = (950, 850);
        self.options_size = (950, 850)
        self.message_size = (950, 850);
        self.admin_size = (950, 850);
        self.login_size = (950, 850)
        self.setMinimumSize(500, 400)

        self.db = DBManager();
        self.manager = RentalManager(self.db)

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
        self.auth_w = AuthWidget(self.manager);
        self.vehicle_list_w = VehicleListWidget(self.manager)
        self.options_w = OptionsWidget(self.manager);
        self.receipt_w = ReceiptWidget()
        self.admin_dashboard_w = AdminDashboardWidget(self.manager);
        self.message_w = MessageWidget(self.manager)

        for w in [self.auth_w, self.vehicle_list_w, self.options_w, self.receipt_w, self.admin_dashboard_w,
                  self.message_w]:
            self.stack.addWidget(w)
        self.stack.setCurrentWidget(self.auth_w)
        self.resize(*self.login_size)

    def setup_connections(self):
        self.auth_w.customer_login_successful.connect(self.on_customer_login);
        self.auth_w.admin_login_successful.connect(self.on_admin_login);
        self.sidebar.logout_requested.connect(self.on_logout);
        self.sidebar.vehicle_list_requested.connect(self.go_to_vehicle_list)
        self.sidebar.message_center_requested.connect(self.go_to_message_center)

        self.vehicle_list_w.proceed_requested.connect(self.go_to_options);
        self.options_w.booking_confirmed.connect(self.on_booking_confirmed)
        self.options_w.back_to_vehicles.connect(self.go_to_vehicle_list);
        self.receipt_w.start_new_rental.connect(self.go_to_vehicle_list)

        # --- MODIFIED: Removed back_to_main connection ---
        self.admin_dashboard_w.signout_requested.connect(self.on_logout)
        # --- END MODIFIED ---

        self.admin_dashboard_w.availability_updated.connect(self.refresh_customer_vehicle_list_in_background)

        self.message_w.message_sent.connect(self.on_message_sent);
        self.message_w.back_to_main.connect(self.go_to_vehicle_list)

    def refresh_customer_vehicle_list_in_background(self):
        self.vehicle_list_w.update_car_list()

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
        self.manager.current_user = {"id": 0, "name": "Administrator", "email": "admin@gmail.com"}  # Admin user

        # --- MODIFIED: Call the reset method to load all txns and clear search bar ---
        self.admin_dashboard_w.sales_tab.handle_reset()
        # --- END MODIFIED ---

        self.admin_dashboard_w.inventory_tab.populate_availability_table()
        self.admin_dashboard_w.messages_tab.populate_message_table()
        self.admin_dashboard_w.inventory_tab.populate_categories_dropdown()

        # --- MODIFIED: Hide sidebar for admin ---
        self.sidebar.hide()
        # --- END MODIFIED ---

        self.stack.setCurrentWidget(self.admin_dashboard_w)

    # --- MODIFIED: Show sidebar only if not admin ---
    def on_customer_login(self, name, email):
        self.vehicle_list_w.update_welcome_message(name);
        self.go_to_vehicle_list();
        self.sidebar.show()  # Show for customer

    # --- END MODIFIED ---

    def closeEvent(self, e):
        self.db.close();
        super().closeEvent(e)


if __name__ == "__main__":
    try:
        plt.switch_backend('QtAgg')
        app = QApplication(sys.argv)

        # --- "DARK MODE" GLOBAL STYLESHEET ---
        app.setStyleSheet("""
            /* ----- Palette (DARK MODE) ----- */
            /*
            --bg-main: #2c3e50;        /* Dark blue/grey app background */
            --bg-content: #34495e;     /* Slightly lighter for content areas */
            --border: #4a627c;         /* Muted border */
            --text-main: #ecf0f1;      /* Light grey/white text */
            --text-light: #bdc3c7;     /* Lighter text for titles */
            --primary: #3498db;        /* Primary blue (Stays the same) */
            --primary-hover: #2980b9;
            --danger: #e74c3c;
            --danger-hover: #c0392b;
            --secondary: #7f8c8d;
            --secondary-hover: #6c7a7b;
            */

            /* ----- Global Defaults ----- */
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
            }

            /* ----- Text & Labels ----- */
            QLabel, QCheckBox {
                font-size: 10pt;
                background-color: transparent;
                color: #ecf0f1;
            }

            /* Make links in QLabels blue */
            QLabel a {
                color: #3498db;
            }

            /* ----- Input Fields ----- */
            QLineEdit, QTextEdit, QComboBox {
                background-color: #34495e;
                color: #ecf0f1;
                padding: 8px;
                border: 1px solid #4a627c;
                border-radius: 4px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #3498db; 
            }
            QLineEdit:read-only {
                background-color: #2c3e50;
            }

            /* Style QComboBox dropdown */
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png); /* You'd need to provide a light arrow icon */
            }
            QComboBox QAbstractItemView {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #4a627c;
                selection-background-color: #3498db;
            }


            /* ----- Content Areas ----- */
            QGroupBox {
                background-color: #34495e;
                border: 1px solid #4a627c;
                border-radius: 5px;
                margin-top: 10px;
                padding: 15px;
                font-size: 10pt;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                color: #bdc3c7;
                font-weight: bold;
            }

            QScrollArea {
                border: none;
                background-color: #34495e;
            }
            QScrollArea > QWidget > QWidget {
                 background-color: #34495e;
            }

            /* ----- Tables ----- */
            QTableWidget {
                background-color: #34495e;
                border: 1px solid #4a627c;
                gridline-color: #4a627c;
                color: #ecf0f1;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                padding: 5px;
                border-bottom: 2px solid #3498db;
                border-right: 1px solid #4a627c;
                font-weight: bold;
                color: #ecf0f1;
            }

            /* ----- Buttons ----- */
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 10pt;
                font-weight: bold;

            }
            QPushButton:hover {
                background-color: #2980b9;
            }

            /* ----- Special Buttons (by objectName) ----- */
            QPushButton#DangerButton {
                background-color: #e74c3c;
            }
            QPushButton#DangerButton:hover {
                background-color: #c0392b;
            }

            QPushButton#SecondaryButton {
                background-color: #7f8c8d;
                font-size: 10px;
                padding: 5px;
                font-weight: normal;
            }
            QPushButton#SecondaryButton:hover {
                background-color: #6c7a7b;
            }

            /* ----- Sidebar (by objectName) ----- */
            /* This section remains almost identical */
            QWidget#Sidebar {
                background-color: #2c3e50;
                border-right: 2px solid #3498db;
            }
            QWidget#Sidebar QLabel {
                color: #ecf0f1;
                font-weight: bold;
                font-size: 11pt;
                background-color: transparent;
            }
            QWidget#Sidebar QPushButton {
                background-color: #34495e;
                color: #ecf0f1;
                padding: 12px 10px;
                border: none;
                text-align: left;
                margin: 5px 10px;
                border-radius: 4px;
                font-weight: normal;
            }
            QWidget#Sidebar QPushButton:hover {
                background-color: #4a627c;
            }
        """)

        window = RentalApp()
        window.show()
        sys.exit(app.exec())
    except ImportError as e:
        sys.exit(
            f"A required library is missing ({e}). Run: pip install pandas matplotlib mysql-connector-python PyQt6 hashlib")
    except Exception as e:
        print(f"An application error occurred: {e}")
import sys
import datetime
import mysql.connector
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget, QRadioButton,
    QGridLayout, QMessageBox, QGroupBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIntValidator, QPixmap
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


class DBManager:

    def __init__(self, host="localhost", user="root", password="", database="car_rental_db_final"):

        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:

            self.conn = mysql.connector.connect(
                host=self.host, user=self.user, password=self.password
            )
            self.cursor = self.conn.cursor()

            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            self.cursor.close()
            self.conn.close()

            self.conn = mysql.connector.connect(
                host=self.host, user=self.user, password=self.password, database=self.database
            )
            self.cursor = self.conn.cursor(dictionary=True)

            self._create_tables()
            self._insert_initial_data()
            print("Database connection successful and tables checked.")
        except mysql.connector.Error as err:
            QMessageBox.critical(None, "Database Error", f"Failed to connect to MySQL: {err}. Ensure XAMPP is running.")
            sys.exit(1)

    def _create_tables(self):

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id VARCHAR(10) PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category_id VARCHAR(10),
                name VARCHAR(100) NOT NULL UNIQUE,
                price_per_day DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                price DECIMAL(10, 2) NOT NULL,
                is_daily BOOLEAN NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                user_name VARCHAR(100),
                user_email VARCHAR(100),
                car_model VARCHAR(100),
                duration INT,
                services_used TEXT,
                final_total DECIMAL(10, 2)
            )
        """)
        self.conn.commit()

    def _insert_initial_data(self):

        categories_data = [
            ('1', '6 Seaters (SUVs, MPVs, Vans)'),
            ('2', '4 Seaters (Sedans & Specialty)')
        ]
        self.cursor.executemany("INSERT IGNORE INTO categories (id, name) VALUES (%s, %s)", categories_data)

        cars_data = [

            ('1', 'Toyota Innova (MPV)', 3200.00),
            ('1', 'Mitsubishi Xpander (MPV)', 2800.00),
            ('1', 'Nissan Terra (SUV)', 4500.00),
            ('1', 'Ford Everest (SUV)', 4300.00),
            ('1', 'Hyundai Staria (Van)', 6000.00),

            ('2', 'Toyota Vios / Honda City', 1750.00),
            ('2', 'Mazda 3', 2200.00),
            ('2', 'Honda Civic Turbo', 2600.00),
            ('2', 'Toyota Camry', 3500.00),
            ('2', 'BMW 3-Series (Luxury)', 5000.00)
        ]
        self.cursor.execute("DELETE FROM cars")
        self.cursor.executemany("INSERT INTO cars (category_id, name, price_per_day) VALUES (%s, %s, %s)",
                                cars_data)

        services_data = [

            ('Insurance and Waivers', 1500.00, False),
            ('RFID Pass (Toll Fees)', 750.00, False),
        ]
        self.cursor.execute("DELETE FROM services")
        self.cursor.executemany("INSERT INTO services (name, price, is_daily) VALUES (%s, %s, %s)",
                                services_data)

        self.conn.commit()

    def get_all_categories(self):
        self.cursor.execute("SELECT id, name FROM categories")
        return {cat['id']: {"name": cat['name']} for cat in self.cursor.fetchall()}

    def get_cars_by_category(self, category_id):
        self.cursor.execute("SELECT name, price_per_day FROM cars WHERE category_id = %s", (category_id,))
        return [Car(c['name'], c['price_per_day']) for c in self.cursor.fetchall()]

    def get_all_services(self):
        self.cursor.execute("SELECT name, price, is_daily FROM services")
        return self.cursor.fetchall()

    def save_transaction(self, txn):

        service_names = ", ".join([f"{s['name']} (₱{s['cost']:,.2f})" for s in txn.services])

        sql = """
            INSERT INTO transactions 
            (timestamp, user_name, user_email, car_model, duration, services_used, final_total)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        data = (
            txn.timestamp,
            txn.user.get('name'),
            txn.user.get('email'),
            txn.car.name,
            txn.duration,
            service_names,
            txn.final_total
        )
        self.cursor.execute(sql, data)
        self.conn.commit()

    def get_all_transactions(self):
        self.cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
        raw_txns = self.cursor.fetchall()

        transactions = []
        for raw in raw_txns:
            dummy_car = Car(raw['car_model'], 0)
            user_data = {"name": raw['user_name'], "email": raw['user_email']}

            services_list = [{"name": raw['services_used'], "cost": 0, "is_daily": False}]

            txn = Transaction(
                user=user_data,
                car=dummy_car,
                duration=raw['duration'],
                services=services_list,
                final_total=raw['final_total']
            )
            txn.timestamp = raw['timestamp']
            transactions.append(txn)

        return transactions

    def close(self):
        if self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()


class Car:
    def __init__(self, name, price_per_day):
        self._name = name
        self._price_per_day = price_per_day

    @property
    def name(self): return self._name

    @property
    def price_per_day(self): return self._price_per_day

    def to_string(self): return f"{self._name} - ₱{self._price_per_day:,.2f} / day"


class Transaction:
    def __init__(self, user, car, duration, services, final_total):
        self.timestamp = datetime.datetime.now()
        self.user = user
        self.car = car
        self.duration = duration
        self.services = services
        self.final_total = final_total


class RentalSystem:
    def __init__(self, db_manager):
        self.db = db_manager
        self.categories = self.db.get_all_categories()
        self.services = self.db.get_all_services()

    def get_cars(self, category_id):
        return self.db.get_cars_by_category(category_id)

    def get_services(self):
        return [
            {"name": svc['name'], "price": svc['price'], "is_daily": bool(svc['is_daily'])}
            for svc in self.services
        ]


def format_peso(amount): return f"₱{amount:,.2f}"


class RentalManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.r_sys = RentalSystem(self.db)
        self.current_user = {"name": "", "email": ""}

    def login(self, name, email): self.current_user = {"name": name, "email": email}

    def logout(self): self.current_user = {"name": "", "email": ""}

    def record_transaction(self, book_data):
        txn = Transaction(user=self.current_user, car=book_data["car"], duration=book_data["duration"],
                          services=book_data["services"], final_total=book_data["final_total"])
        self.db.save_transaction(txn)

    def get_all_transactions(self):
        return self.db.get_all_transactions()


class BaseWidget(QWidget):
    def __init__(self): super().__init__()

    def create_label(self, text, bold=False, size=12):
        lbl = QLabel(text);
        if bold: lbl.setFont(QFont("Arial", size, QFont.Weight.Bold));
        return lbl


class PasscodeWidget(BaseWidget):
    passcode_entered = pyqtSignal(str)

    def __init__(self):
        super().__init__();
        layout = QVBoxLayout(self);
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter);
        layout.setSpacing(15)
        layout.addWidget(self.create_label("Administrator Access", True, 16), alignment=Qt.AlignmentFlag.AlignCenter);
        layout.addWidget(QLabel("Enter Passcode:"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.pass_in = QLineEdit();
        self.pass_in.setEchoMode(QLineEdit.EchoMode.Password);
        self.pass_in.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px; max-width: 200px;");
        self.pass_in.returnPressed.connect(self.send_passcode);
        layout.addWidget(self.pass_in, alignment=Qt.AlignmentFlag.AlignCenter)
        button = QPushButton("Submit");
        button.clicked.connect(self.send_passcode);
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)

    def send_passcode(self):
        code = self.pass_in.text();
        self.passcode_entered.emit(code);
        self.pass_in.clear()


class AuthWidget(BaseWidget):
    auth_success = pyqtSignal(str, str)

    def __init__(self): super().__init__(); self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self);
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter);
        layout.setSpacing(12)
        title = self.create_label("Welcome! Please Login or Sign Up", True, 18);
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.name_in = QLineEdit();
        self.name_in.setPlaceholderText("Enter your full name")
        self.email_in = QLineEdit();
        self.email_in.setPlaceholderText("Enter your email")
        layout.addWidget(QLabel("Your Name:"));
        layout.addWidget(self.name_in)
        layout.addWidget(QLabel("Email Address:"));
        layout.addWidget(self.email_in)
        cont_btn = QPushButton("Continue to Rentals");
        cont_btn.clicked.connect(self.handle_auth);
        layout.addWidget(cont_btn)

    def handle_auth(self):
        name = self.name_in.text().strip();
        email = self.email_in.text().strip()
        if not (name and email): return QMessageBox.warning(self, "Error", "Please fill in all fields.")
        self.auth_success.emit(name, email)


class CategoryWidget(BaseWidget):
    category_selected = pyqtSignal(str);
    logout_requested = pyqtSignal();
    hist_req_prompt = pyqtSignal()

    def __init__(self, name, r_sys):
        super().__init__()
        self.user_name = name
        self.r_sys = r_sys
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(15)
        self.welcome_lbl = self.create_label(f"Hello, Mr. {self.user_name}!", True, 20)
        layout.addWidget(self.welcome_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Select a category:")
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        for key, cat in self.r_sys.categories.items():
            btn = QPushButton(f"{key}: {cat['name']}")
            btn.setProperty("category_key", key)
            btn.clicked.connect(lambda checked, k=key: self.category_selected.emit(k))
            layout.addWidget(btn)

        hist_btn = QPushButton("Admin: View Transactions")
        hist_btn.clicked.connect(self.hist_req_prompt.emit)
        layout.addWidget(hist_btn)
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout_requested.emit)
        layout.addWidget(logout_btn)
        layout.addStretch(1)

    def update_welcome_message(self, name):
        self.user_name = name
        self.welcome_lbl.setText(f"Hello, Mr. {self.user_name}!")


class CarSelectionWidget(BaseWidget):
    services_ready = pyqtSignal(dict)
    back_to_categories = pyqtSignal()

    def __init__(self, r_sys):
        super().__init__()
        self.r_sys = r_sys
        self.cat_key = None
        self.car_radios = []
        self.service_checkboxes = []
        self.setup_ui()

    def reset_state(self):

        self.dur_in.setText("1")
        for checkbox in self.service_checkboxes:
            checkbox.setChecked(False)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(10)

        self.title_lbl = self.create_label("", True, 18)
        self.layout.addWidget(self.title_lbl)

        self.car_list = QWidget()
        self.car_layout = QVBoxLayout(self.car_list)
        self.car_group = QGroupBox("Select Car:")
        self.car_group.setLayout(self.car_layout)
        self.layout.addWidget(self.car_group)

        options_container = QWidget()
        options_layout = QVBoxLayout(options_container)
        options_layout.setSpacing(15)

        dur_layout = QHBoxLayout()
        self.dur_in = QLineEdit("1")
        self.dur_in.setValidator(QIntValidator())
        self.dur_in.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px; max-width: 80px;")
        dur_layout.addWidget(QLabel("Duration (days):"))
        dur_layout.addWidget(self.dur_in)
        dur_layout.addStretch(1)
        options_layout.addLayout(dur_layout)

        self.service_summary_group = QGroupBox("Available Add-ons:")
        self.service_summary_group.setStyleSheet("""
            QGroupBox {font-weight: bold; margin-top: 10px; padding-top: 20px; border: 1px solid #d1d5db; border-radius: 6px;}
            QGroupBox::title {subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; color: #3b82f6;}
            QCheckBox {padding: 5px; spacing: 10px; font-size: 13px;}
        """)
        self.service_summary_layout = QVBoxLayout(self.service_summary_group)
        self.service_summary_layout.setContentsMargins(10, 20, 10, 10)

        self.service_checkboxes.clear()
        for svc in self.r_sys.get_services():
            checkbox = QCheckBox(f"{svc['name']} ({format_peso(svc['price'])} {'/ day' if svc['is_daily'] else ''})")
            checkbox.setProperty("svc_data", svc)
            self.service_summary_layout.addWidget(checkbox)
            self.service_checkboxes.append(checkbox)

        options_layout.addWidget(self.service_summary_group)
        self.layout.addWidget(options_container)

        confirm_btn = QPushButton("Confirm Booking")
        confirm_btn.clicked.connect(self.confirm_selection)
        self.layout.addWidget(confirm_btn)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.back_to_categories.emit)
        self.layout.addWidget(back_btn)
        self.layout.addStretch(1)

    def update_view(self, cat_key):
        self.cat_key = cat_key
        cat = next((v for k, v in self.r_sys.categories.items() if k == cat_key), None)
        if not cat: return
        self.title_lbl.setText(cat["name"])

        for i in reversed(range(self.car_layout.count())):
            widget = self.car_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        self.car_radios.clear()
        cars = self.r_sys.get_cars(self.cat_key)

        for i, car in enumerate(cars):
            radio = QRadioButton(car.to_string())
            radio.setProperty("index", i)
            self.car_layout.addWidget(radio)
            if i == 0: radio.setChecked(True)
            self.car_radios.append(radio)

    def confirm_selection(self):
        selected = next((r for r in self.car_radios if r.isChecked()), None)
        if not selected: return QMessageBox.warning(self, "Error", "Select a car first.")

        dur = self.dur_in.text()
        if not dur.isdigit() or int(dur) <= 0: return QMessageBox.warning(self, "Error", "Invalid duration.")

        car_list = self.r_sys.get_cars(self.cat_key)
        car = car_list[selected.property("index")]

        days = int(dur)
        base_total = car.price_per_day * days

        final_services = []
        services_total = 0
        for checkbox in self.service_checkboxes:
            if checkbox.isChecked():
                svc = checkbox.property("svc_data")

                svc_cost = svc['price'] * days if svc['is_daily'] else svc['price']
                services_total += svc_cost
                final_services.append({"name": svc["name"], "cost": svc_cost, "is_daily": svc["is_daily"]})

        final_total = base_total + services_total

        booking_data = {
            "car": car,
            "duration": days,
            "base_total": base_total,
            "services": final_services,
            "final_total": final_total
        }
        self.services_ready.emit(booking_data)


class ReceiptWidget(BaseWidget):
    start_new_rental = pyqtSignal()

    def __init__(self):
        super().__init__();
        self.setup_ui()

    def setup_ui(self):
        lyt = QVBoxLayout(self);
        lyt.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        conf_lbl = self.create_label("BOOKING CONFIRMED", True, 15);
        lyt.addWidget(conf_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        lyt.addWidget(self.create_label("--- Transaction Details ---", True, 10))
        self.r_area = QWidget();
        r_lyt = QGridLayout(self.r_area);
        r_lyt.setSpacing(8)
        self.name_lbl = self.create_label("");
        r_lyt.addWidget(self.name_lbl, 0, 0, 1, 2)
        r_lyt.addWidget(QLabel("Car Model:"), 1, 0);
        self.car_lbl = QLabel();
        r_lyt.addWidget(self.car_lbl, 1, 1, Qt.AlignmentFlag.AlignRight)
        r_lyt.addWidget(QLabel("Rental Days:"), 2, 0);
        self.dur_lbl = QLabel();
        r_lyt.addWidget(self.dur_lbl, 2, 1, Qt.AlignmentFlag.AlignRight)
        r_lyt.addWidget(QLabel("Base Cost:"), 3, 0);
        self.base_total_lbl = QLabel();
        r_lyt.addWidget(self.base_total_lbl, 3, 1, Qt.AlignmentFlag.AlignRight)
        self.svc_title_lbl = self.create_label("--- ADD-ONS ---", True, 10);
        r_lyt.addWidget(self.svc_title_lbl, 4, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        self.svc_wig = QWidget();
        self.svc_lyt = QVBoxLayout(self.svc_wig);
        self.svc_lyt.setContentsMargins(0, 0, 0, 0);
        r_lyt.addWidget(self.svc_wig, 5, 0, 1, 2)
        r_lyt.addWidget(QLabel(""), 6, 0, 1, 2);
        self.total_lbl = self.create_label("", True, 16);
        r_lyt.addWidget(self.create_label("FINAL TOTAL:", True, 14), 7, 0);
        r_lyt.addWidget(self.total_lbl, 7, 1, Qt.AlignmentFlag.AlignRight)
        lyt.addWidget(self.r_area);
        new_btn = QPushButton("Start New Rental");
        new_btn.clicked.connect(self.start_new_rental.emit);
        lyt.addWidget(new_btn);
        lyt.addStretch(1)

    def update_receipt(self, name, book_data):
        car = book_data["car"];
        dur = book_data["duration"];
        final_total = book_data["final_total"];
        base_total = book_data["base_total"];
        svcs = book_data["services"]
        self.name_lbl.setText(f"Client: {name}");
        self.car_lbl.setText(car.name);
        self.dur_lbl.setText(f"{dur} Day{'s' if dur > 1 else ''}");
        self.base_total_lbl.setText(format_peso(base_total));
        self.total_lbl.setText(format_peso(final_total))
        while self.svc_lyt.count():
            item = self.svc_lyt.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child_item = item.layout().takeAt(0)
                    if child_item.widget():
                        child_item.widget().deleteLater()
        if svcs:
            self.svc_title_lbl.show()
            for svc in svcs:
                item_lyt = QHBoxLayout();
                item_lyt.addWidget(QLabel(f"- {svc['name']}"));
                item_lyt.addWidget(QLabel(format_peso(svc['cost'])), alignment=Qt.AlignmentFlag.AlignRight);
                self.svc_lyt.addLayout(item_lyt)
        else:
            self.svc_title_lbl.hide();
            self.svc_lyt.addWidget(QLabel("(No extra services selected)"),
                                   alignment=Qt.AlignmentFlag.AlignCenter)


class TransactionHistoryWidget(BaseWidget):
    back_to_categories = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_txns = []
        self.setup_ui()

    def generate_sales_chart(self, txns):
        data = []
        for txn in txns:
            data.append({
                'timestamp': txn.timestamp,
                'final_total': txn.final_total
            })
        df = pd.DataFrame(data)

        if df.empty:
            return None

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')

        weekly_sales = df['final_total'].resample('W').sum().fillna(0)

        weekly_labels = [
            f"{week.strftime('%b %d')}"
            for week in weekly_sales.index
        ]

        plt.figure(figsize=(9, 5))
        plt.plot(weekly_labels, weekly_sales.values, marker='o', color='#1e40af', linewidth=2)

        def peso_formatter(x, pos):

            return f'₱{x:,.0f}'

        formatter = FuncFormatter(peso_formatter)
        plt.gca().yaxis.set_major_formatter(formatter)

        plt.title('Total Rental Sales Revenue by Week', fontsize=14, weight='bold')
        plt.xlabel('Week Ending', fontsize=11)
        plt.ylabel('Total Sales Revenue (in PHP)', fontsize=11)
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.yticks(fontsize=9)
        plt.grid(axis='both', linestyle='--', alpha=0.6)
        plt.tight_layout()

        filename = 'sales_chart.png'
        plt.savefig(filename)
        plt.close()
        return filename

    def setup_ui(self):
        lyt = QVBoxLayout(self);
        lyt.setSpacing(10)
        title_lbl = self.create_label("Transaction History & Sales Report", True, 18);
        lyt.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.graph_container = QWidget()
        self.graph_layout = QVBoxLayout(self.graph_container)
        self.graph_lbl = QLabel("Weekly Sales Trend will be displayed here.")
        self.graph_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graph_layout.addWidget(self.graph_lbl)
        lyt.addWidget(self.graph_container)

        lyt.addWidget(self.create_label("--- Transaction List ---", True, 14), alignment=Qt.AlignmentFlag.AlignCenter)

        self.table = QTableWidget();
        self.table.setColumnCount(6);
        self.table.setHorizontalHeaderLabels(["Date", "Client", "Car Model", "Add-ons", "Days", "Total Price"])
        self.table.setStyleSheet(
            "QHeaderView::section { background-color: #e2e8f0; font-weight: bold; padding: 4px; } QTableWidget {gridline-color: #cbd5e1;}")

        head = self.table.horizontalHeader()
        head.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch);
        head.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        head.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lyt.addWidget(self.table)

        back_btn = QPushButton("← Back to Categories");
        back_btn.clicked.connect(self.back_to_categories.emit);
        lyt.addWidget(back_btn)

    def refresh_graph_display(self):
        if not self.current_txns:
            self.graph_lbl.setText("No transactions yet to generate sales chart.")
            return

        chart_file = self.generate_sales_chart(self.current_txns)

        if chart_file:
            pixmap = QPixmap(chart_file)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.graph_container.width(), 300,
                                              Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
                self.graph_lbl.setPixmap(scaled_pixmap)
                self.graph_lbl.setText("")
            else:
                self.graph_lbl.setText("Error loading sales chart image.")

    def update_table(self, txns):
        self.current_txns = txns
        self.table.setRowCount(0)
        if not txns:
            self.table.setRowCount(1);
            item = QTableWidgetItem("No transactions recorded yet.");
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter);
            self.table.setItem(0, 0, 1, 6);
            return

        self.table.setRowCount(len(txns))
        for row, tx in enumerate(txns):
            date_str = tx.timestamp.strftime("%Y-%m-%d %H:%M")
            total_item = QTableWidgetItem(format_peso(tx.final_total));
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            svc_names = tx.services[0]['name'] if tx.services and tx.services[0]['name'] else "None"

            self.table.setItem(row, 0, QTableWidgetItem(date_str));
            self.table.setItem(row, 1, QTableWidgetItem(tx.user.get('name', 'N/A')))
            self.table.setItem(row, 2, QTableWidgetItem(tx.car.name));
            self.table.setItem(row, 3, QTableWidgetItem(svc_names))
            self.table.setItem(row, 4, QTableWidgetItem(str(tx.duration)));
            self.table.setItem(row, 5, total_item)

        self.table.resizeRowsToContents();
        self.table.resizeColumnsToContents()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_graph_display()


class RentalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Car Rentals (OOP + MySQL)")
        self.initial_size = (550, 600)
        self.setMinimumSize(self.initial_size[0], self.initial_size[1])

        self.db_manager = DBManager()
        self.manager = RentalManager(self.db_manager)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.init_widgets()
        self.setup_connections()

    def init_widgets(self):
        self.auth_wig = AuthWidget()
        self.cat_wig = CategoryWidget("", self.manager.r_sys)
        self.car_wig = CarSelectionWidget(self.manager.r_sys)
        self.receipt_wig = ReceiptWidget()
        self.hist_wig = TransactionHistoryWidget()
        self.passcode_wig = PasscodeWidget()

        self.stack.addWidget(self.auth_wig)
        self.stack.addWidget(self.cat_wig)
        self.stack.addWidget(self.car_wig)
        self.stack.addWidget(self.receipt_wig)
        self.stack.addWidget(self.hist_wig)
        self.stack.addWidget(self.passcode_wig)

        self.stack.setCurrentWidget(self.auth_wig)

    def setup_connections(self):
        self.auth_wig.auth_success.connect(self.on_login)
        self.cat_wig.category_selected.connect(self.go_to_car)
        self.cat_wig.logout_requested.connect(self.on_logout)
        self.cat_wig.hist_req_prompt.connect(lambda: self.stack.setCurrentWidget(self.passcode_wig))

        self.car_wig.services_ready.connect(self.on_booking_confirmed)
        self.car_wig.back_to_categories.connect(lambda: self.stack.setCurrentWidget(self.cat_wig))

        self.receipt_wig.start_new_rental.connect(lambda: self.stack.setCurrentWidget(self.cat_wig))

        self.passcode_wig.passcode_entered.connect(self.check_passcode)

        self.hist_wig.back_to_categories.connect(self.restore_and_go_to_categories)

    def restore_and_go_to_categories(self):
        self.showNormal()
        self.stack.setCurrentWidget(self.cat_wig)

    def on_login(self, name, email):
        self.manager.login(name, email)
        self.cat_wig.update_welcome_message(name)
        self.stack.setCurrentWidget(self.cat_wig)

    def on_logout(self):
        self.manager.logout()
        self.auth_wig.name_in.clear()
        self.auth_wig.email_in.clear()
        self.stack.setCurrentWidget(self.auth_wig)

    def go_to_car(self, cat_key):
        self.showNormal()
        self.car_wig.reset_state()
        self.car_wig.update_view(cat_key)
        self.stack.setCurrentWidget(self.car_wig)

    def on_booking_confirmed(self, book_data):
        self.manager.record_transaction(book_data)
        self.receipt_wig.update_receipt(self.manager.current_user['name'], book_data)
        self.stack.setCurrentWidget(self.receipt_wig)

    def check_passcode(self, code):
        if code == "123":
            self.showMaximized()
            self.hist_wig.update_table(self.manager.get_all_transactions())
            self.stack.setCurrentWidget(self.hist_wig)
            self.hist_wig.refresh_graph_display()
        else:
            QMessageBox.critical(self, "Access Denied", "Incorrect passcode.")
            self.stack.setCurrentWidget(self.cat_wig)

    def closeEvent(self, event):
        self.db_manager.close()
        super().closeEvent(event)


if __name__ == "__main__":
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        import mysql.connector

        plt.switch_backend('QtAgg')
    except ImportError as e:
        print(
            f"A required library is missing: {e}. Please ensure 'pandas', 'matplotlib', and 'mysql-connector-python' are installed.")
        print("Run: pip install pandas matplotlib mysql-connector-python")
        sys.exit(1)
    except Exception as e:
        print(f"Error setting Matplotlib backend or other issue: {e}")

    app = QApplication(sys.argv)
    window = RentalApp()
    window.show()
    sys.exit(app.exec())
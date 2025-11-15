import sys
import datetime
import pymysql  # --- CHANGED: Using PyMySQL ---
from PyQt6.QtWidgets import QMessageBox

# Use relative imports for project files
from .utils import hash_password
from .models import Car, Transaction

# --- DATABASE CONFIGURATION ---
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""
DB_NAME = "car_rental_db"  # The database name you created


class DBManager:
    def __init__(self):
        self.conn, self.cursor = None, None
        self.connect()

    def connect(self):
        try:
            # --- CHANGED: Connect using PyMySQL ---
            self.conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                # --- CHANGED: Use a dictionary cursor ---
                cursorclass=pymysql.cursors.DictCursor
            )
            # We get the cursor from the connection
            self.cursor = self.conn.cursor()

            self._insert_initial_data()

        except pymysql.Error as err:  # --- CHANGED: Error type ---
            QMessageBox.critical(None, "Database Error",
                                 f"Failed to connect to MySQL database: {err}.\n"
                                 f"Is XAMPP (MySQL) running? Is the database '{DB_NAME}' created?")
            sys.exit(1)

    def _insert_initial_data(self):
        try:
            categories = [('1', '6 Seaters (SUVs, MPVs, Vans)'), ('2', '4 Seaters (Sedans & Specialty)')]
            # --- CHANGED: PyMySQL's executemany is a bit different, so we loop ---
            for category in categories:
                try:
                    self.cursor.execute("INSERT INTO categories (id, name) VALUES (%s, %s)", category)
                except pymysql.IntegrityError:
                    pass  # Ignore if it already exists

            cars = [('1', 'Toyota Innova (MPV)', 3200.00), ('1', 'Mitsubishi Xpander (MPV)', 2800.00),
                    ('1', 'Nissan Terra (SUV)', 4500.00), ('1', 'Ford Everest (SUV)', 4300.00),
                    ('1', 'Hyundai Staria (Van)', 6000.00), ('2', 'Toyota Vios / Honda City', 1750.00),
                    ('2', 'Mazda 3', 2200.00), ('2', 'Honda Civic Turbo', 2600.00),
                    ('2', 'Toyota Camry', 3500.00), ('2', 'BMW 3-Series (Luxury)', 5000.00)]

            for car in cars:
                try:
                    self.cursor.execute("INSERT INTO cars (category_id, name, price_per_day) VALUES (%s, %s, %s)", car)
                except pymysql.IntegrityError:
                    pass  # Ignore if it already exists

            self.cursor.execute("SELECT COUNT(*) AS count FROM users WHERE email = %s", ("test@user.com",))
            if self.cursor.fetchone()['count'] == 0:
                self.cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                                    ("Test User", "test@user.com", hash_password("password")))

            services = [('Insurance and Waivers', 1500.00, 0), ('RFID Pass (Toll Fees)', 750.00, 0)]
            for service in services:
                try:
                    self.cursor.execute("INSERT INTO services (name, price, is_daily) VALUES (%s, %s, %s)", service)
                except pymysql.IntegrityError:
                    pass  # Ignore if it already exists

            self.conn.commit()
        except pymysql.Error as err:
            print(f"DB Warning (Initial Data): {err}")
            self.conn.rollback()

    # --- ALL METHODS BELOW ARE UPDATED FOR PyMySQL ---
    # (Mainly just changing error types)

    def register_user(self, name, email, password_hash):
        try:
            self.cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                                (name, email, password_hash))
            self.conn.commit()
            return True
        except pymysql.IntegrityError:  # Specific error for UNIQUE constraint
            return "Email already registered."
        except pymysql.Error as err:
            return str(err)

    def login_user(self, email, password_hash):
        self.cursor.execute("SELECT id, name, email FROM users WHERE email = %s AND password_hash = %s",
                            (email, password_hash))
        return self.cursor.fetchone()

    def get_all_cars_data(self, only_available=False):
        query = """
            SELECT c.id, c.name, c.price_per_day, c.is_available, c.category_id, cat.name as category_name
            FROM cars c
            JOIN categories cat ON c.category_id = cat.id
        """
        if only_available: query += " WHERE c.is_available = 1"
        self.cursor.execute(query + " ORDER BY c.category_id, c.name")
        return self.cursor.fetchall()

    def get_cars_by_category(self, category_id, only_available=False):
        query = "SELECT name, price_per_day, is_available FROM cars WHERE category_id = %s"
        params = [category_id]
        if only_available:
            query += " AND is_available = 1"
        self.cursor.execute(query, params)
        # We use bool() because MySQL returns 1 or 0
        return [Car(c['name'], c['price_per_day'], bool(c['is_available'])) for c in self.cursor.fetchall()]

    def update_car_availability(self, car_id, is_available):
        self.cursor.execute("UPDATE cars SET is_available = %s WHERE id = %s", (int(is_available), car_id))
        self.conn.commit()

    def get_all_categories(self):
        self.cursor.execute("SELECT id, name FROM categories ORDER BY id")
        return self.cursor.fetchall()

    def add_car(self, category_id, name, price):
        try:
            self.cursor.execute(
                "INSERT INTO cars (category_id, name, price_per_day, is_available) VALUES (%s, %s, %s, %s)",
                (category_id, name, price, 1)
            )
            self.conn.commit()
            return True
        except pymysql.IntegrityError:
            return f"A car with the name '{name}' already exists."
        except pymysql.Error as err:
            return str(err)

    def edit_car(self, car_id, name, price, category_id):
        try:
            self.cursor.execute(
                "UPDATE cars SET name = %s, price_per_day = %s, category_id = %s WHERE id = %s",
                (name, price, category_id, car_id)
            )
            self.conn.commit()
            return True
        except pymysql.IntegrityError:
            return f"A car with the name '{name}' already exists."
        except pymysql.Error as err:
            return str(err)

    def delete_car(self, car_id):
        try:
            self.cursor.execute("DELETE FROM cars WHERE id = %s", (car_id,))
            self.conn.commit()
            return True
        except pymysql.IntegrityError as err:
            return "Cannot delete car. It is linked to existing bookings or transactions."
        except pymysql.Error as err:
            return str(err)

    def get_all_services(self):
        self.cursor.execute("SELECT name, price, is_daily FROM services ORDER BY name")
        return self.cursor.fetchall()

    def get_all_services_with_ids(self):
        self.cursor.execute("SELECT id, name, price, is_daily FROM services ORDER BY name")
        return self.cursor.fetchall()

    def add_service(self, name, price, is_daily):
        try:
            self.cursor.execute(
                "INSERT INTO services (name, price, is_daily) VALUES (%s, %s, %s)",
                (name, price, int(is_daily))
            )
            self.conn.commit()
            return True
        except pymysql.IntegrityError:
            return f"A service with the name '{name}' already exists."
        except pymysql.Error as err:
            return str(err)

    def delete_service(self, service_id):
        try:
            self.cursor.execute("DELETE FROM services WHERE id = %s", (service_id,))
            self.conn.commit()
            return True
        except pymysql.Error as err:
            return str(err)

    def save_transaction(self, txn):
        services = ", ".join([f"{s['name']} (₱{s['cost']:,.2f})" for s in txn.services])
        data = (txn.user.get('id'), txn.timestamp, txn.user.get('name'), txn.user.get('email'),
                txn.car.name, txn.duration, services, txn.final_total)
        self.cursor.execute(
            "INSERT INTO transactions (user_id, timestamp, user_name, user_email, car_model, duration, services_used, final_total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            data)
        self.conn.commit()

    def save_message(self, name, email, message):
        self.cursor.execute(
            "INSERT INTO messages (timestamp, user_name, user_email, message_text) VALUES (%s, %s, %s, %s)",
            (datetime.datetime.now(), name, email, message))
        self.conn.commit()

    def _build_transactions_from_rows(self, rows):
        transactions = []
        for raw in rows:
            dummy_car = Car(raw['car_model'], 0)
            user_data = {
                "id": raw.get('user_id'),
                "name": raw['user_name'],
                "email": raw['user_email']
            }
            services_text = raw.get('services_used', '')
            services = [{"name": services_text, "cost": 0}] if services_text else []
            txn = Transaction(user=user_data, car=dummy_car, duration=raw.get('duration', 0), services=services,
                              final_total=raw.get('final_total', 0.0))

            # PyMySQL returns datetime objects, so no conversion is needed
            txn.timestamp = raw.get('timestamp')
            transactions.append(txn)
        return transactions

    def get_all_transactions(self):
        self.cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
        return self._build_transactions_from_rows(self.cursor.fetchall())

    def get_transactions_by_user_id(self, user_id):
        self.cursor.execute("SELECT * FROM transactions WHERE user_id = %s ORDER BY timestamp DESC", (user_id,))
        return self._build_transactions_from_rows(self.cursor.fetchall())

    def get_all_messages(self):
        self.cursor.execute("SELECT * FROM messages ORDER BY timestamp DESC")
        return self.cursor.fetchall()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
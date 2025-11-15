from .utils import hash_password
from .models import Transaction
from .database import DBManager


class RentalManager:
    def __init__(self, db_manager: DBManager):  # Use type hinting
        self.db = db_manager
        self.current_user = {"id": None, "name": "", "email": ""}

    def get_categories(self): return self.db.get_all_categories()

    def get_cars(self, cat_id): return self.db.get_cars_by_category(cat_id, only_available=True)

    def get_services(self): return self.db.get_all_services()

    def register(self, name, email, password):
        return self.db.register_user(name, email, hash_password(password))

    def login(self, email, password):
        user_data = self.db.login_user(email, hash_password(password))
        if user_data:
            # user_data is a dict-like Row object
            self.current_user = {"id": user_data['id'], "name": user_data['name'], "email": user_data['email']}
            return True
        return False

    def logout(self):
        self.current_user = {"id": None, "name": "", "email": ""}

    def record_transaction(self, data):
        txn = Transaction(user=self.current_user, car=data["car"], duration=data["duration"], services=data["services"],
                          final_total=data["final_total"])
        self.db.save_transaction(txn)

    def save_message(self, name, email, message):
        self.db.save_message(name, email, message)

    def get_all_cars_for_admin(self): return self.db.get_all_cars_data(only_available=False)

    def add_new_car(self, category_id, name, price):
        return self.db.add_car(category_id, name, price)

    def edit_car(self, car_id, name, price, category_id):
        return self.db.edit_car(car_id, name, price, category_id)

    def delete_car(self, car_id):
        return self.db.delete_car(car_id)

    def update_car_unit_availability(self, car_id, is_available):
        self.db.update_car_availability(car_id, is_available)

    def get_all_services_with_ids(self):
        return self.db.get_all_services_with_ids()

    def add_new_service(self, name, price, is_daily):
        return self.db.add_service(name, price, is_daily)

    def delete_service(self, service_id):
        return self.db.delete_service(service_id)

    def get_all_transactions(self): return self.db.get_all_transactions()

    def get_transactions_by_user_id(self, user_id):
        return self.db.get_transactions_by_user_id(user_id)

    def get_all_messages(self): return self.db.get_all_messages()
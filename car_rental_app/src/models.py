import datetime
from .utils import format_peso # Use relative import

# --- Data Classes ---

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
        self.user, self.car, self.duration, self.services, self.final_total = user, car, duration, services, final_total
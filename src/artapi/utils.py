import time
import string
import random

class Utils:
    @staticmethod
    def generate_order_number():
        timestamp = int(time.time())  # Current timestamp as an integer
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))  # Random string of 6 characters
        return f"{timestamp}{random_str}"

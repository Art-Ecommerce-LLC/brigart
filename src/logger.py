import logging
import sys
import os
# Add the parent directory of src to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging.handlers import RotatingFileHandler
import os

# Ensure the log directory exists
log_dir = "log"
os.makedirs(log_dir, exist_ok=True)

# Set up logging
logger = logging.getLogger("brig_api")
logger.setLevel(logging.INFO)

# Log to a file, with rotation
log_file = os.path.join(log_dir, "app.log")
handler = RotatingFileHandler(log_file, maxBytes=2000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Function to retrieve logs
def get_logs() -> str:
    if not os.path.exists(log_file):
        with open(log_file, "w") as f:
            f.write("")
    with open(log_file, "r") as f:
        return f.read()

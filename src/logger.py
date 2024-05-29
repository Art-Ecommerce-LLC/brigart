import logging
from logging.handlers import RotatingFileHandler

# Set up logging
logger = logging.getLogger("brig_api")
logger.setLevel(logging.INFO)

# Log to a file, with rotation
handler = RotatingFileHandler("log/app.log", maxBytes=2000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Function to retrieve logs
def get_logs() -> str:
    with open("log/app.log", "r") as f:
        return f.read()

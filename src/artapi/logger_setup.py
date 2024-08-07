# src/artapi/logger_setup.py
import logging
import os
from logging.handlers import RotatingFileHandler

# Ensure the log directory exists
log_dir = "log"
os.makedirs(log_dir, exist_ok=True)

# Set up the main logger
logger = logging.getLogger("brig_api")
logger.setLevel(logging.INFO)

# Log to a file, with rotation
log_file = os.path.join(log_dir, "app.log")
file_handler = RotatingFileHandler(log_file, maxBytes=2000, backupCount=5)
formatter = logging.Formatter('{asctime} - {name} - {levelname} - {message}', style='{')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


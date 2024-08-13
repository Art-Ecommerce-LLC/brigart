import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from src.artapi.nocodb_connector import Noco
import requests
from src.artapi.noco_config import (
    ADMIN_DEVELOPER_EMAIL, 
    ADMIN_DEVELOPER_NUMBER,
    SMTP_SERVER,
    SMTP_PORT,
    APP_PASSWORD,
    ERROR405_BOT_TOKEN,
    ERROR405_CHAT_ID
)

# Ensure the log directory exists
log_dir = "log"
os.makedirs(log_dir, exist_ok=True)

class ErrorLogger(logging.Handler):
    def __init__(self) -> None:
        super().__init__() 
    
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno > logging.INFO:  # Post only warnings, errors, and critical logs
            payload = self.format_payload(record)
            self.send_email(payload)
            self.send_telegram_message(payload)
    
    def format_payload(self, record: logging.LogRecord) -> dict:
        error = {
            "timestamp": self.format_time(record),
            "logger_name": record.name,
            "level": record.levelname,
            "message": record.getMessage()
        }
        ticket_assignment = {
            "developer_email": ADMIN_DEVELOPER_EMAIL,
            "developer_number": ADMIN_DEVELOPER_NUMBER
        }

        status = "open"

        payload = {
            "error": error,
            "ticket_assignment": ticket_assignment,
            "status": status
        }

        return payload

    def format_time(self, record: logging.LogRecord) -> str:
        record_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        return record_time

    def send_email(self, payload: dict) -> None:
        try:
            message = MIMEText(f"Error occurred:\n\n{payload['error']}")
            message['Subject'] = f"Error Notification: {payload['error']['level']}"
            message['From'] = ADMIN_DEVELOPER_EMAIL
            message['To'] = ADMIN_DEVELOPER_EMAIL

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(ADMIN_DEVELOPER_EMAIL, APP_PASSWORD)
                server.sendmail(ADMIN_DEVELOPER_EMAIL, ADMIN_DEVELOPER_EMAIL, message.as_string())
        except:
            pass

    def send_telegram_message(self, payload: dict) -> None:
        try:
            url = f"https://api.telegram.org/bot{ERROR405_BOT_TOKEN}/sendMessage"
            message = f"Error occurred:\n{payload['error']['timestamp']}\n{payload['error']['message']}"
            data = {
                'chat_id': ERROR405_CHAT_ID,
                'text': message
            }
            response = requests.post(url, json=data)
            response.raise_for_status()
        except:
            pass
# Function to setup the logger with the NocoDB connection
def setup_logger() -> logging.Logger:
    logger = logging.getLogger("brig_api")
    logger.setLevel(logging.INFO)

    # Log to a file, with rotation
    log_file = os.path.join(log_dir, "app.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=2000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Add custom error logger to the main logger
    error_logger = ErrorLogger()
    logger.addHandler(error_logger)

    return logger

# Initialize logger with a callable that provides the NocoDB connection
# Function to retrieve logs
def get_logs() -> str:
    log_file = os.path.join(log_dir, "app.log")
    if not os.path.exists(log_file):
        with open(log_file, "w") as f:
            f.write("")
    with open(log_file, "r") as f:
        return f.read()

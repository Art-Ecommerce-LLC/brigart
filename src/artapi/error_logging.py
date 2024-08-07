# src/artapi/error_logging.py
import logging
from logging import LogRecord
from datetime import datetime
from src.artapi.nocodb_connector import get_noco_db
import smtplib
from email.mime.text import MIMEText
from src.artapi.noco_config import (
    ADMIN_DEVELOPER_EMAIL, 
    ADMIN_DEVELOPER_NUMBER,
    SMTP_SERVER,
    SMTP_PORT,
    APP_PASSWORD,
    ERROR405_BOT_TOKEN,
    ERROR405_CHAT_ID
)
import requests

class ErrorLogger(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.db_connector = get_noco_db()  # Assuming get_noco_db() returns a database connection or client
    
    def emit(self, record: LogRecord) -> None:
        if record.levelno > logging.INFO:  # Post only warnings, errors, and critical logs
            payload = self.format_payload(record)
            self.send_to_db(payload)
            self.send_email(payload)
            self.send_telegram_message(payload)
    
    def format_payload(self, record: LogRecord) -> dict:
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

    def format_time(self, record: LogRecord) -> str:
        record_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        return record_time
    
    def send_to_db(self, payload: dict) -> None:
        self.db_connector.post_error_message(payload)

    def send_email(self, payload: dict) -> None:
        message = MIMEText(f"Error occurred:\n\n{payload['error']}")
        message['Subject'] = f"Error Notification: {payload['error']['level']}"
        message['From'] = ADMIN_DEVELOPER_EMAIL
        message['To'] = ADMIN_DEVELOPER_EMAIL

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(ADMIN_DEVELOPER_EMAIL, APP_PASSWORD)
            server.sendmail(ADMIN_DEVELOPER_EMAIL, ADMIN_DEVELOPER_EMAIL, message.as_string())

    def send_telegram_message(self, payload: dict) -> None:
        url = f"https://api.telegram.org/bot{ERROR405_BOT_TOKEN}/sendMessage"
        message = f"Error occurred:\n{payload['error']['timestamp']}\n{payload['error']['message']}"
        data = {
            'chat_id': ERROR405_CHAT_ID,
            'text': message
        }
        response = requests.post(url, json=data)
        response.raise_for_status()


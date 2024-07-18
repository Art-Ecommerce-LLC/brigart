import time
import string
import random
from src.artapi.noco import Noco
from src.artapi.logger import logger
from datetime import datetime, timezone
import asyncio
import base64
import tempfile
from io import BytesIO
import os

class Utils:

    @staticmethod
    def generate_order_number():
        timestamp = int(time.time())  # Current timestamp as an integer
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))  # Random string of 6 characters
        return f"{timestamp}{random_str}"
    
    @staticmethod
    def get_version():
        return str(int(time.time()))

    @staticmethod
    async def delete_expired_sessions():
        while True:
            try:
                noco_db = Noco()  # Instantiate your database connection
                cookie_data = noco_db.get_cookie_data()
                sessions = cookie_data.sessionids
                created_ats = cookie_data.created_ats
                current_time = datetime.now(timezone.utc)

                for session_id, creation_time_str in zip(sessions, created_ats):
                    session_creation_time = datetime.fromisoformat(creation_time_str.replace('Z', '+00:00'))

                    elapsed_time = (current_time - session_creation_time).total_seconds()
                    if elapsed_time > 900:  # 15 minutes = 900 seconds
                        noco_db.delete_session_cookie(session_id)
                        logger.info(f"Deleted expired session {session_id}")

            except Exception as e:
                logger.error(f"Error deleting expired sessions: {e}")

            # Wait for 1 minute before checking again
            await asyncio.sleep(900)

    @staticmethod
    def decode_data_uri(data_uri: str, title: str) -> str:
        try:
            header, encoded = data_uri.split(",", 1)
            data = base64.b64decode(encoded)
            
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, f"{title}.png")
            
            # Write the image content to the file with the custom name
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(data)
            
            return temp_file_path
        except Exception as e:
            logger.error(f"Failed to decode data URI: {e}")

    @staticmethod
    def delete_temp_file(path: str):
        try:
            os.remove(path)
        except Exception as e:
            logger.error(f"Failed to delete temp file: {e}")

    @staticmethod
    def decode_data_uri_to_BytesIO(data_uri: str) -> BytesIO:
        try:
            header, encoded = data_uri.split(",", 1)
            data = base64.b64decode(encoded)
            return BytesIO(data)
        except Exception as e:
            logger.error(f"Failed to decode data URI: {e}")

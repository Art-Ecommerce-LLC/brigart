import time
from .noco import Noco
from requests.exceptions import ConnectionError

class NocoDBManager:
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds

    def __init__(self):
        self.noco_db = self._create_noco_instance()

    def _create_noco_instance(self):
        """
        Create a new instance of NocoDB and return it.
        """
        try:
            noco_instance = Noco()
            return noco_instance
        except ConnectionError as e:
            raise

    def _handle_connection_error(self):
        """
        Handle connection errors by retrying the connection.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                self.noco_db = self._create_noco_instance()
                return
            except ConnectionError as e:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    raise

    def get_noco_db(self):
        """
        Get the NocoDB instance, ensuring the session is valid.
        """
        return self.noco_db

# Instantiate NocoDBManager
noco_db_manager = NocoDBManager()

def get_noco_db():
    """
    Get the NocoDB instance from the manager.
    """
    return noco_db_manager.get_noco_db()
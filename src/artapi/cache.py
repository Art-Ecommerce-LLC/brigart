import json
from functools import lru_cache
from src.artapi.logger import logger
from src.artapi.noco import get_nocodb_data, get_nocodb_icons, get_nocodb_email_data

class Cache:
    def __init__(self) -> None:
        self.data_uris = None
        self.titles = None

@lru_cache(maxsize=128)
def load_nocodb_data() -> dict:
    try:
        logger.info("Loading NoCoDB data")
        data = json.loads(get_nocodb_data())
        logger.info("NoCoDB data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB data: {e}")
        raise


@lru_cache(maxsize=128)
def load_nocodb_icon_data() -> dict:
    try:
        logger.info("Loading NoCoDB icon data")
        data = json.loads(get_nocodb_icons())
        logger.info("NoCoDB icon data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB icon data: {e}")
        raise

@lru_cache(maxsize=128)
def load_nocodb_email_data() -> dict:
    try:
        logger.info("Loading NoCoDB email data")
        data = json.loads(get_nocodb_email_data())
        logger.info("NoCoDB email data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB email data: {e}")
        raise
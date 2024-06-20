from functools import lru_cache
from src.artapi.logger import logger
from src.artapi.noco import Noco

@lru_cache(maxsize=128)
def load_nocodb_data() -> dict:
    try:
        logger.info("Loading NoCoDB data")
        data = Noco.get_artwork_data()
        logger.info("NoCoDB data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB data: {e}")
        raise

@lru_cache(maxsize=128)
def load_nocodb_email_data() -> dict:
    try:
        logger.info("Loading NoCoDB email data")
        data = Noco.get_email_data()
        logger.info("NoCoDB email data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB email data: {e}")
        raise

@lru_cache(maxsize=128)
def load_nocodb_icon_data() -> dict:
    try:
        logger.info("Loading NoCoDB icon data")
        data = Noco.get_icon_data()
        logger.info("NoCoDB icon data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB icon data: {e}")
        raise

@lru_cache(maxsize=128)
def load_nocodb_key_data() -> dict:
    try:
        logger.info("Loading NoCoDB key data")
        data = Noco.get_key_data()
        logger.info("NoCoDB key data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB key data: {e}")
        raise

@lru_cache(maxsize=128)
def load_nocodb_contact_data() -> dict:
    try:
        logger.info("Loading NoCoDB contact data")
        data = Noco.get_contact_data()
        logger.info("NoCoDB contact data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB contact data: {e}")
        raise

@lru_cache(maxsize=128)
def load_nocodb_order_data() -> dict:
    try:
        logger.info("Loading NoCoDB order data")
        data = Noco.get_order_data()
        logger.info("NoCoDB order data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB order data: {e}")
        raise

@lru_cache(maxsize=128)
def load_nocodb_content_data() -> dict:
    try:
        logger.info("Loading NoCoDB content data")
        data = Noco.get_content_data()
        logger.info("NoCoDB content data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB content data: {e}")
        raise

@lru_cache(maxsize=128)
def load_nocodb_cookie_data() -> dict:
    try:
        logger.info("Loading NoCoDB cookie data")
        data = Noco.get_cookie_data()
        logger.info("NoCoDB cookie data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading NoCoDB cookie data: {e}")
        raise

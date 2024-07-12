import asyncio
from datetime import datetime, timedelta, timezone
from src.artapi.logger import logger
from src.artapi.noco import Noco, NOCODB_TABLE_MAP

async def remove_expired_cookies():
    while True:
        try:
            cookies_data = Noco.get_cookie_data()
            current_time = datetime.now(timezone.utc)  # Make current_time timezone-aware
            for i, created_at in enumerate(cookies_data.created_ats):
                cookie_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))  # This is already timezone-aware
                if current_time - cookie_time > timedelta(minutes=30):
                    Noco.delete_nocodb_table_data(NOCODB_TABLE_MAP.cookies_table, cookies_data.Id[i])
                    logger.info(f"Deleted expired cookie with session ID {cookies_data.sessionids[i]}")
            await asyncio.sleep(1800)  # Sleep for half a minute
        except Exception as e:
            logger.error(f"Error in remove_expired_cookies: {e}")
            await asyncio.sleep(1800)  # Sleep for half a minute

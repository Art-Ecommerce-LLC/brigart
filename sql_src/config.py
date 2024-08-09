import dotenv
import os

dotenv_path = dotenv.find_dotenv()

dotenv.load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("database_url")

NOCODB_PATH = os.getenv("nocodb_path")
NOCODB_XC_TOKEN = os.getenv("nocodb_xc_token")

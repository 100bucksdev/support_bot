import os
from dotenv import load_dotenv

load_dotenv()

SUPPORT_TELEGRAM_BOT_TOKEN = os.getenv("API_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_LOGIN_KEY = os.getenv("SECRET_LOGIN_KEY")
BASE_SERVER_URL = "http://127.0.0.1:8000/"

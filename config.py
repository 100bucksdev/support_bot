import os
from dotenv import load_dotenv

load_dotenv()

SUPPORT_TELEGRAM_BOT_TOKEN = os.getenv("SUPPORT_TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_LOGIN_KEY = os.getenv("SECRET_LOGIN_KEY")
BASE_SERVER_URL = os.getenv("BASE_SERVER_URL")
CHANNEL_ID= os.getenv("CHANNEL_ID")
# BASE_SERVER_URL = "http://django:8000/"

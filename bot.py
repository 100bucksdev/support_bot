from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import API_BOT_TOKEN


bot = Bot(token=API_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

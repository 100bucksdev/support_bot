from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from config import BASE_SERVER_URL
from DataBase.database import Database
from Hendlers.inline_keyboard_handler import CallOperatorStates
import requests

from server_requests import make_request

in_chat_handler = Router()
db = Database()


@in_chat_handler.message(CallOperatorStates.in_chat)
async def chatting_handler(message: Message):
    if any([message.photo, message.video, message.document, message.audio,
            message.voice, message.animation, message.video_note, message.sticker]):
        await message.answer("The bot does not know how to work with files or images, if you need it notify the developers! The user will not see your files")
        return
    telegram_id = message.from_user.id
    text = message.text
    data = {
        'operator_telegram_id': telegram_id,
        'message': text
    }

    await make_request(data, message)


@in_chat_handler.message()
async def handle_text(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    text = message.text
    operator = db.get_operator(telegram_id=telegram_id)
    if operator.is_busy and operator.busy_with_chat:
        await state.set_state(CallOperatorStates.in_chat)
    data = {
        'operator_telegram_id': telegram_id,
        'message': text
    }
    await make_request(data, message)


















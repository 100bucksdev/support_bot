import requests
from aiogram.types import ReplyKeyboardRemove

from config import BASE_SERVER_URL


async def make_request(data, message):
    url = f'{BASE_SERVER_URL}api/v1/chatbot/chat/operator/send-message/'

    response = requests.post(url, json=data)

    response_json = response.json()
    if response_json.get('message') == 'chat_not_exist':
        await message.answer('❌ The message was not delivered because the chat does not exist', reply_markup=ReplyKeyboardRemove())

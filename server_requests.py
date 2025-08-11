import aiohttp
from aiogram.types import ReplyKeyboardRemove

from config import BASE_SERVER_URL


async def make_request(data, message):
    url = f'{BASE_SERVER_URL}api/v1/chatbot/chat/operator/send-message/'

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                response_json = await response.json()

    except Exception as e:
        print(f"Error making request: {e}")
        return

    if response_json.get('message') == 'chat_not_exist':
        await message.answer('❌ The message was not delivered because the chat does not exist',
                             reply_markup=ReplyKeyboardRemove())
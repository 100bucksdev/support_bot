from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from DataBase.database import Database
from server_requests import make_request

markup_handler = Router()
db = Database()

@markup_handler.message(F.text == '❌ End chat')
async def end_chat_handler(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    await state.clear()
    data = {
        'info': "operator_end_chat",
        'operator_telegram_id': telegram_id
    }
    await make_request(data, message)
    await message.answer('Chat with user ended', reply_markup=ReplyKeyboardRemove())


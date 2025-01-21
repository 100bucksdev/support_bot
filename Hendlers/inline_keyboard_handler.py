from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery

from DataBase.database import Database
from Keyboards.markup import operator_in_chat_keyboard
from server_requests import make_request

inline_handler = Router()
db = Database()

class CallOperatorStates(StatesGroup):
    in_chat = State()

@inline_handler.callback_query(F.data.startswith('accept_'))
async def accept_request(query: CallbackQuery, state: FSMContext):
    telegram_id = query.from_user.id
    room_name = query.data.split('_')[-1]
    db.update_operator(telegram_id=telegram_id, busy_with_chat=room_name, is_busy=True)

    await query.message.edit_text("✅ You have successfully accepted the chat with the user.\n"
                                  f"💬 Chat ID: {room_name}", reply_markup=None)
    chat_history = db.get_chat_history(room_name)
    await query.message.answer('🗃 History of users communication with AI:')
    for message in chat_history:
        await query.message.answer(message, reply_markup=operator_in_chat_keyboard)
    await state.set_state(CallOperatorStates.in_chat)
    data = {'info': 'operator_accept_chat', "operator_name": db.get_operator(telegram_id=telegram_id).name, 'operator_telegram_id': telegram_id}
    await make_request(data, query.message)
    await query.answer()






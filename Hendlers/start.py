from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from aiogram import Router
from aiogram.filters import CommandStart, CommandObject

from DataBase.database import Database
from Keyboards.markup import default_keyboard
from config import SECRET_LOGIN_KEY

start = Router()

db = Database()


class RegistrationState(StatesGroup):
    waiting_for_full_name = State()

@start.message(CommandStart())
async def start_handler(message: Message, state: FSMContext, command: CommandObject):
    telegram_id = message.from_user.id
    args = command.args

    operator = db.get_operator(telegram_id)
    if not operator:
        if not args or args != SECRET_LOGIN_KEY:
            await message.answer('Wrong code')
            return

        db.add_operator(telegram_id=telegram_id)
        operator = db.get_operator(telegram_id)

    if operator.name is None:
        await message.answer('👋 Hello, we found your account, but you haven’t added your full name.\n'
                             'Please send your full name (e.g., Andzej Bartosko).')
        await state.set_state(RegistrationState.waiting_for_full_name)
        return

    await message.answer(f'👋 Hello, {operator.name}, you are already registered. Here is your data:\n'
                         f'🆔 ID: {operator.custom_id}\n'
                         f'📊 Status: {"Busy" if operator.is_busy else "Not Busy"}\n'
                         f'💬 Busy with chat: {"Not Busy" if operator.busy_with_chat is None else operator.busy_with_chat}', reply_markup=default_keyboard)


@start.message(RegistrationState.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text


    if len(full_name.split()) < 2:
        await message.answer('Please enter your full name (e.g., Andzej Bartosko).')
        return

    telegram_id = message.from_user.id
    db.update_operator(telegram_id, name=full_name)

    await state.clear()

    await message.answer(f'Thank you, {full_name}! Your registration is now complete.', reply_markup=default_keyboard)



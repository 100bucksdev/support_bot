from aiogram.fsm.state import StatesGroup, State


class AddNewPatternsStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer = State()
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from Keyboards.inline import is_continue
from config import CHAT_PROCESS_SERVICE_URL
from external_service import make_request
from states.add_new_patterns import AddNewPatternsStates

new_pattern_router = Router()

SIM_THRESHOLD = 0.68

@new_pattern_router.message(Command('add_new_patterns'))
async def add_new_pattern_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🖊 Send Question:")
    await state.set_state(AddNewPatternsStates.waiting_for_question)

@new_pattern_router.message(AddNewPatternsStates.waiting_for_question)
async def handle_question(message: Message, state: FSMContext):
    question = message.text
    response = await make_request(base_url=CHAT_PROCESS_SERVICE_URL, url='pattern', params={'question': question})
    await state.update_data(question=question)
    if not isinstance(response, dict) or response.get('status') != 200:
        await message.answer("❌ Error occurred. Please try again later.")
        await state.clear()
        return
    body = response.get('body') or []
    hit = body[0] if body else None
    if hit and hit.get('score', 0) > SIM_THRESHOLD:
        await state.update_data(existing_hit=hit)
        await message.answer(
            f"ℹ️ Pattern with same question already exists:\n"
            f"➖ Question: {hit.get('question', '')}\n"
            f"➖ Answer: {hit.get('answer', '')}\n"
            f"✨ Similarity: {hit.get('score', 0) * 100:.2f}%\n",
            reply_markup=is_continue(hit.get('uuid', ''))
        )
        return
    await state.set_state(AddNewPatternsStates.waiting_for_answer)
    await message.answer("🖊 Send Answer:")

@new_pattern_router.message(AddNewPatternsStates.waiting_for_answer)
async def handle_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    question = data.get("question")
    answer = message.text
    force_save = data.get("force_save", False)
    data = {
        'question': question,
        'answer': answer,
        'force_save': force_save
    }
    response = await make_request(base_url=CHAT_PROCESS_SERVICE_URL,method='POST', url='pattern', data=data)
    if not isinstance(response, dict) or response.get('status') != 200:
        await message.answer('❌ Something went wrong. Please try again later.')
    await message.answer("✅ Done.")
    await state.clear()

@new_pattern_router.callback_query(F.data == 'continue')
async def continue_handler(query: CallbackQuery, state: FSMContext):
    await state.update_data(force_save=True)
    await state.set_state(AddNewPatternsStates.waiting_for_answer)
    await query.message.answer("🖊 Send Answer:")
    await query.answer()

@new_pattern_router.callback_query(F.data == 'cancel')
async def cancel_handler(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.answer("❌ Canceled.")
    await query.answer()

@new_pattern_router.callback_query(F.data.startswith('delete_and_add_new_'))
async def delete_and_add_new_handler(query: CallbackQuery, state: FSMContext):
    pattern_question = query.data.split('delete_and_add_new_', 1)[1]
    resp = await make_request(base_url=CHAT_PROCESS_SERVICE_URL, method='DELETE', url='pattern', params={'uuid': pattern_question})
    if not isinstance(resp, dict) or resp.get('status') != 200:
        await query.message.answer("❌ Delete failed. Try again later.")
        await state.clear()
        await query.answer()
        return
    await state.update_data(force_save=True)
    await state.set_state(AddNewPatternsStates.waiting_for_answer)
    await query.message.answer("🖊 Send Answer:")
    await query.answer()





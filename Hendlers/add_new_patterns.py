import html
import re
from io import BytesIO

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from Keyboards.inline import is_continue, add_new_patterns_way, save_patterns_from_txt
from config import CHAT_PROCESS_SERVICE_URL
from external_service import make_request
from states.add_new_patterns import AddNewPatternsStates

new_pattern_router = Router()

SIM_THRESHOLD = 0.68
MAX_DUPLICATES_SHOW=10

@new_pattern_router.message(Command('add_new_patterns'))
async def add_new_pattern_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Choose method:", reply_markup=add_new_patterns_way())

@new_pattern_router.callback_query(F.data == 'add_patterns_from_txt')
async def add_using_txt_file(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await state.clear()
    text = (
        "Send <b>.txt</b> file with questions and answers\n"
        "This file should look like this:\n"
        "<pre><code>Q: Hello how are you?\n"
        "A: I am fine.\n\n"
        "Q: Where are you?\n"
        "A: I am in the city.\n\n"
        "And so on...</code></pre>\n"
        "Waiting for file"
    )
    await query.message.edit_text(text, reply_markup=None)
    await state.set_state(AddNewPatternsStates.waiting_for_file)

@new_pattern_router.message(AddNewPatternsStates.waiting_for_file)
async def handle_file(message: Message, state: FSMContext):
    doc = message.document
    if not doc or not ((doc.mime_type and doc.mime_type.startswith("text/plain")) or (doc.file_name and doc.file_name.lower().endswith(".txt"))):
        await message.answer("Please send a <b>.txt</b> file with questions and answers")
        return

    processing_msg = await message.answer("Processing file...")

    buffer = BytesIO()
    try:
        await message.bot.download(doc, destination=buffer)
    except Exception:
        file_obj = await message.bot.get_file(doc.file_id)
        await message.bot.download(file_obj, destination=buffer)

    text = buffer.getvalue().decode("utf-8", errors="ignore")
    blocks = re.split(r"\r?\n\s*\r?\n", text.strip())

    patterns: list[dict[str, str]] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        q_line = next((l for l in lines if l.lower().startswith("q:")), None)
        a_line = next((l for l in lines if l.lower().startswith("a:")), None)
        if q_line and a_line:
            patterns.append({"question": q_line[2:].lstrip(), "answer": a_line[2:].lstrip()})

    await state.update_data(patterns=patterns)
    status_msg = await processing_msg.edit_text(
        f"Found {len(patterns)} question–answer pairs ✅\n"
        f"Checking similar questions in the database…"
    )

    repeated_questions = []
    for pattern in patterns:
        try:
            resp = await make_request(base_url=CHAT_PROCESS_SERVICE_URL, url='pattern', params={'question': pattern['question']})
        except Exception:
            continue
        if not isinstance(resp, dict) or resp.get('status') != 200:
            continue
        body = resp.get('body') or []
        hit = body[0] if body else None
        if hit and hit.get('score', 0) > SIM_THRESHOLD:
            repeated_questions.append({'saved_pattern': hit, 'new_pattern': pattern})

    await state.update_data(repeated_questions=repeated_questions)

    if not repeated_questions:
        await status_msg.edit_text(
            f"Found {len(patterns)} pairs ✅\n"
            f"No similar questions found. You can proceed to save them."
        )
        return

    lines = [
        f"Found {len(patterns)} pairs ✅",
        f"{len(repeated_questions)} similar existing pattern(s) detected:",
        ""
    ]

    for i, item in enumerate(repeated_questions[:MAX_DUPLICATES_SHOW], start=1):
        hit = item['saved_pattern']
        new_q = html.escape(item['new_pattern'].get('question', ''))
        old_q = html.escape(hit.get('question', ''))
        old_a = html.escape(hit.get('answer', ''))
        score = hit.get('score', 0) * 100
        lines.append(
            f"{i}) <b>New Q</b>: {new_q}\n"
            f"   <b>Existing Q</b>: {old_q}\n"
            f"   <b>Existing A</b>: {old_a}\n"
            f"   <b>Similarity</b>: {score:.2f}%\n"
        )

    if len(repeated_questions) > MAX_DUPLICATES_SHOW:
        lines.append(f"...and {len(repeated_questions) - MAX_DUPLICATES_SHOW} more similar pattern(s).")

    await status_msg.edit_text("\n".join(lines), reply_markup=save_patterns_from_txt())

@new_pattern_router.callback_query(F.data == 'save_patterns_from_txt')
async def save_patterns_from_txt_handler(query: CallbackQuery, state: FSMContext):
    await query.answer()
    data = await state.get_data()
    patterns = data.get('patterns')
    if not patterns:
        await query.message.answer("Error occur try again later.")
        return
    await query.message.edit_text('Saving patterns...', reply_markup=None)
    for pattern in patterns:
        data = {
            'question': pattern['question'],
            'answer': pattern['answer'],
            'force_save': True
        }
        response = await make_request(base_url=CHAT_PROCESS_SERVICE_URL, method='POST', url='pattern', data=data)
        if response.get('status') != 200:
            await query.message.answer('Error while saving.')
    await query.message.edit_text('Successfully saved.')


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





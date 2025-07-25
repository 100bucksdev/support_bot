from typing import List, Dict, Any, Optional

from aiogram.types import Message

from Keyboards.inline import send_answer_to_chat
from bot import bot
from config import CHAT_PROCESS_SERVICE_URL, CHAT_BOT_SERVICE_URL
from external_service import make_request

THRESHOLD = 0.68

async def process_new_business_message(message: Message) -> Optional[str]:
    connection = await bot.get_business_connection(message.business_connection_id)
    data = {
        "message": message.text,
        "sender": "client" if message.from_user.id != connection.user.id else "staff",
        "chat_with_user_id": message.chat.id,
        "message_id": message.message_id
    }
    new_message_response = await make_request(url=f'account/user/{connection.user.id}/chat/{message.chat.id}/message', method='POST',
                       data=data)
    if new_message_response.get("status") != 200:
        return None



    if data['sender'] == 'staff':
        return None
    print(data['sender'])
    print('process_new_business_message')

    message_from_client_id: int = new_message_response.get("body").get("id")


    params = {"question": message.text}
    response = await make_request(base_url=CHAT_PROCESS_SERVICE_URL, params=params, url="pattern")
    if response.get("status") != 200:
        return None
    body: List[Dict[str, Any]] = response.get("body") or []
    if not body:
        return None

    top_answers = body[:3]
    best = top_answers[0]
    score = float(best.get("score") or 0)
    messages: List[Dict[str, Any]] = []

    if score > THRESHOLD:
        bot_message = await bot.send_message(connection.user.id, f"ℹ️ A suitable answer to the user question was found in the database:\n"
                                                      f" - Question: {message.text}\n"
                                                      f" - Answer: {best.get('answer')}\n"
                                                      f" - Score: {round(score * 100)}%\n"
                                                      f"✨ Generating a response that is appropriate to the context...")

        lm_resp = await make_request(url=f"account/user/{connection.user.id}/chat/{message.chat.id}/last-messages", params={"count": 5})
        if lm_resp.get("status") == 200:
            messages = lm_resp.get("body") or []
    else:
        return None

    print(messages)
    prompt_text = generate_text_for_assistant(message.text, messages, top_answers)
    print(prompt_text)

    answer_resp = await make_request(base_url=CHAT_BOT_SERVICE_URL, url="answer-generator", method="POST", data={"text": prompt_text})
    if answer_resp.get("status") != 200:
        await bot.edit_message_text('❌ Unexpected error occurred while generating an answer.\n'
                                    'Are you want to sent this response to user?', chat_id=bot_message.chat.id, message_id=bot_message.message_id)
        return None
    data = {
        'ai_response': answer_resp.get("body").get("message"),
        'question_message_id': message_from_client_id
    }
    saved_ai_response = await make_request(url='ai-response', method="POST", data=data)
    if saved_ai_response.get("status") != 200:
        return None
    else:
        ai_response_id = saved_ai_response.get("body").get("id")

    await bot.edit_message_text(f'ℹ️ Successfully generated an answer.\n'
                                f' - Question: {message.text}\n'
                                f' - Answer: {answer_resp.get("body").get("message")}\n'
                                f'Are you want to send this answer?', chat_id=bot_message.chat.id,
                                message_id=bot_message.message_id,
                                reply_markup=send_answer_to_chat(ai_response_id, message.chat.id, message.business_connection_id))
    answer_body = answer_resp.get("body")

    return answer_body.get("message")


def generate_text_for_assistant(question: str, messages: List[Dict[str, Any]], top_answers: List[Dict[str, Any]]) -> str:
    ctx_lines: List[str] = ["Context:"]
    for m in messages:
        role = m.get("sender")
        text = m.get("message_text")
        ctx_lines.append(f"{role}: {text}")
    ctx_lines.append("")
    ctx_lines.append(f"Question: {question}")
    ctx_lines.append("")

    pattern_lines: List[str] = []
    for i, p in enumerate(top_answers, 1):
        q = p.get("q") or p.get("question") or ""
        a = p.get("a") or p.get("answer") or ""
        s = p.get("score")
        s_str = f"{round(float(s) * 100)}%" if isinstance(s, (int, float)) else "N/A"
        pattern_lines.append(f"{i} Pattern: Q: {q} A: {a} Score: {s_str}")

    return "\n".join(ctx_lines + pattern_lines)

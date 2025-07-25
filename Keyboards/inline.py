from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def choose_auction_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='COPART', callback_data=f'auction_copart')
            ],
            [
                InlineKeyboardButton(text='IAAI', callback_data=f'auction_iaai')
            ]
        ]
    )

def is_continue(uuid:str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Continue ⏩', callback_data=f'continue'),
                InlineKeyboardButton(text='Cancel ❌', callback_data=f'cancel')
            ],
            [
                InlineKeyboardButton(text='🗑 Delete this pattern and add new', callback_data=f'delete_and_add_new_{uuid}')
            ]
        ]
    )

def send_answer_to_chat(ai_response_id: int, chat_with_client_id: int, connection_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Send response to chat', callback_data=f'send|answer|{ai_response_id}|{chat_with_client_id}|{connection_id}')
            ]
        ]
    )

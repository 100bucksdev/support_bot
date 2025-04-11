from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

operator_in_chat_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='❌ End chat'),
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Text with user"
)

default_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='🆕 Generate post'),
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Select action"
)
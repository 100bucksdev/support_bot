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

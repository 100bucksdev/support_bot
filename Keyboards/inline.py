from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def choose_auction_keyboard(lot_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='COPART', callback_data=f'auction_copart_{lot_id}')
            ],
            [
                InlineKeyboardButton(text='IAAI', callback_data=f'auction_iaai_{lot_id}')
            ]
        ]
    )

def add_photos(lot_id: str, auction: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Add 3 Photos', callback_data=f'add_photos_{lot_id}_{auction}')
            ],
            [
                InlineKeyboardButton(text='Publish', callback_data=f'publish_{lot_id}_{auction}')
            ]
        ]
    )

def yes_keyboard(lot_id: str, auction: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Yes', callback_data=f'yes_{lot_id}_{auction}')
            ]
        ]
    )
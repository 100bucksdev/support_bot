

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InputMediaPhoto

from Keyboards.inline import choose_auction_keyboard, add_photos, yes_keyboard
from Keyboards.markup import default_keyboard
from PostGenerator.generator import PostGenerator
from config import CHANNEL_ID

generate_post_handler = Router()

class GeneratePostStates(StatesGroup):
    wait_for_lot_id = State()

@generate_post_handler.message(F.text=='🆕 Generate post')
async def generate_post(message: Message, state: FSMContext):
    await message.answer('Send lot ID')
    await state.set_state(GeneratePostStates.wait_for_lot_id)

@generate_post_handler.message(GeneratePostStates.wait_for_lot_id)
async def handle_lot_id(message: Message, state: FSMContext):
    lot_id = message.text
    if not lot_id.isdigit():
        await message.answer('Invalid lot ID. Please send a valid lot ID.')
        await state.set_state(GeneratePostStates.wait_for_lot_id)
        return
    await message.answer('Choose auction:', reply_markup=choose_auction_keyboard(lot_id))

@generate_post_handler.callback_query(F.data.startswith('auction_'))
async def handle_auction_selection(query: CallbackQuery, state: FSMContext):
    auction_lot_id = query.data.replace('auction_', '').split('_')
    auction = auction_lot_id[0]
    lot_id = auction_lot_id[1]
    generator = PostGenerator(lot_id, auction)
    if generator.calculator_data is None or generator.lot_data is None:
        await query.message.answer('Invalid Auction.')
        await query.answer()
        await state.clear()
        return
    text = generator.generate_text()
    await query.message.edit_text(text, reply_markup=add_photos(lot_id, auction))
    await query.answer()
    await state.clear()

@generate_post_handler.callback_query(F.data.startswith('add_photos_'))
async def handle_add_photos(query: CallbackQuery):
    auction_lot_id = query.data.replace('add_photos_', '').split('_')
    lot_id = auction_lot_id[0]
    auction = auction_lot_id[1]
    generator = PostGenerator(lot_id, auction)
    if generator.calculator_data is None or generator.lot_data is None:
        await query.message.answer('Invalid Auction.')
        await query.answer()
        return

    await query.message.delete()

    text = generator.generate_text()
    images_urls = generator.get_first_three_images()
    if images_urls:
        media = []
        for i, url in enumerate(images_urls[:3]):
            if i == 0:
                media.append(InputMediaPhoto(media=url, caption=text))
            else:
                media.append(InputMediaPhoto(media=url))
        await query.message.answer_media_group(media=media)
        await query.message.answer('Publish?',reply_markup=yes_keyboard(lot_id, auction))
    await query.answer()

@generate_post_handler.callback_query(F.data.startswith('publish_'))
async def handle_publish_request(query: CallbackQuery):
    auction_lot_id = query.data.replace('publish_', '').split('_')
    lot_id = auction_lot_id[0]
    auction = auction_lot_id[1]
    generator = PostGenerator(lot_id, auction)
    if generator.calculator_data is None or generator.lot_data is None:
        await query.message.answer('Invalid Auction.')
        await query.answer()
        return
    text = generator.generate_text()
    await query.bot.send_message(
        chat_id=CHANNEL_ID,
        text=text
    )
    await query.message.answer('Post published to channel (text only)!', reply_markup=default_keyboard)
    await query.answer()


@generate_post_handler.callback_query(F.data.startswith('yes_'))
async def handle_publish(query: CallbackQuery):
    auction_lot_id = query.data.replace('yes_', '').split('_')
    lot_id = auction_lot_id[0]
    auction = auction_lot_id[1]
    generator = PostGenerator(lot_id, auction)
    if generator.calculator_data is None or generator.lot_data is None:
        await query.message.answer('Invalid Auction.')
        await query.answer()
        return

    text = generator.generate_text()
    images_urls = generator.get_first_three_images()
    if images_urls:
        media = []
        for i, url in enumerate(images_urls[:3]):
            if i == 0:
                media.append(InputMediaPhoto(media=url, caption=text))
            else:
                media.append(InputMediaPhoto(media=url))
        # Post to the specific channel
        await query.bot.send_media_group(
            chat_id=CHANNEL_ID,
            media=media
        )
        await query.message.answer('Post published to channel!', reply_markup=default_keyboard)
    else:
        # Optionally handle case with no images
        await query.bot.send_message(
            chat_id=CHANNEL_ID,
            text=text
        )
        await query.message.answer('Post published to channel (text only)!', reply_markup=default_keyboard)

    await query.answer()






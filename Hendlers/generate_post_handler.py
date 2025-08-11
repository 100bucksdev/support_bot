import os
import tempfile

import aiohttp
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, \
    FSInputFile

from Keyboards.inline import choose_auction_keyboard
from PostGenerator.generator import PostGenerator
from config import CHANNEL_ID

generate_post_handler = Router()


class GeneratePostStates(StatesGroup):
    wait_for_lot_id = State()
    wait_for_auction_selection = State()
    wait_for_photos_decision = State()
    wait_for_comment_decision = State()
    wait_for_comment = State()
    wait_for_publish_confirmation = State()

def yes_no_keyboard(prefix):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Yes", callback_data=f"{prefix}_yes"),
         InlineKeyboardButton(text="No", callback_data=f"{prefix}_no")]
    ])

@generate_post_handler.message(F.text == "🆕 Generate post")
async def generate_post(message: Message, state: FSMContext):
    await message.answer("Send Lot ID:")
    await state.set_state(GeneratePostStates.wait_for_lot_id)


@generate_post_handler.message(GeneratePostStates.wait_for_lot_id)
async def handle_lot_id(message: Message, state: FSMContext):
    lot_id = message.text
    if not lot_id.isdigit():
        await message.answer("Wrong Lot ID. Please send a valid ID.")
        return
    await state.update_data(lot_id=lot_id)
    await message.answer("Choose auction:", reply_markup=choose_auction_keyboard())
    await state.set_state(GeneratePostStates.wait_for_auction_selection)

@generate_post_handler.callback_query(GeneratePostStates.wait_for_auction_selection, F.data.startswith("auction_"))
async def handle_auction_selection(query: CallbackQuery, state: FSMContext):
    auction = query.data.split("_")[1]
    data = await state.get_data()
    lot_id = data["lot_id"]
    generator = PostGenerator(lot_id, auction)
    await generator.initialize()

    if generator.calculator_data is None or generator.lot_data is None:
        await query.message.answer("Wrong auction or lot ID. Please try again.")
        await query.answer()
        return
    await state.update_data(auction=auction, generator=generator)
    await query.message.edit_text("Add 3 Photos?", reply_markup=yes_no_keyboard("photos"))
    await state.set_state(GeneratePostStates.wait_for_photos_decision)
    await query.answer()


@generate_post_handler.callback_query(GeneratePostStates.wait_for_photos_decision, F.data.in_(["photos_yes", "photos_no"]))
async def handle_photos_decision(query: CallbackQuery, state: FSMContext):
    include_photos = query.data == "photos_yes"
    await state.update_data(include_photos=include_photos)
    await query.message.edit_text("Want add comment?", reply_markup=yes_no_keyboard("comment"))
    await state.set_state(GeneratePostStates.wait_for_comment_decision)
    await query.answer()

@generate_post_handler.callback_query(GeneratePostStates.wait_for_comment_decision, F.data.in_(["comment_yes", "comment_no"]))
async def handle_comment_decision(query: CallbackQuery, state: FSMContext):
    if query.data == "comment_yes":
        await query.message.edit_text("Send your comment:")
        await state.set_state(GeneratePostStates.wait_for_comment)
    else:
        await show_preview(query, state)
    await query.answer()


@generate_post_handler.message(GeneratePostStates.wait_for_comment)
async def handle_comment(message: Message, state: FSMContext):
    comment = message.text
    await state.update_data(comment=comment)
    await show_preview(message, state)

async def show_preview(message_or_query, state: FSMContext):
    data = await state.get_data()
    include_photos = data.get("include_photos", False)
    comment = data.get("comment", "")
    generator = data["generator"]

    text = generator.generate_text(comment)

    if include_photos:
        images_urls = generator.get_first_three_images()
        if images_urls:
            media = []
            temp_files = []  # Track temp files for cleanup
            async with aiohttp.ClientSession() as session:
                for i, url in enumerate(images_urls[:3]):
                    try:
                        # Check if the image URL is accessible
                        async with session.get(url) as response:
                            if response.status == 200:
                                # Read image data
                                image_data = await response.read()
                                # Create a temporary file to store the image
                                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                                temp_file.write(image_data)
                                temp_file_path = temp_file.name
                                temp_file.close()  # Explicitly close the file handle
                                temp_files.append(temp_file_path)  # Track for cleanup

                                # Create FSInputFile from the temporary file
                                image_file = FSInputFile(path=temp_file_path, filename=f"image_{i}.jpg")
                                if i == 0:
                                    media.append(InputMediaPhoto(media=image_file, caption=text))
                                else:
                                    media.append(InputMediaPhoto(media=image_file))
                            else:
                                print(f"Failed to fetch image from {url}: Status {response.status}")
                                continue
                    except Exception as e:
                        print(f"Error fetching image from {url}: {e}")
                        continue

            if media:
                try:
                    await message_or_query.bot.send_media_group(
                        chat_id=message_or_query.from_user.id,
                        media=media
                    )
                finally:
                    # Clean up temporary files
                    for temp_file_path in temp_files:
                        try:
                            if os.path.exists(temp_file_path):
                                os.unlink(temp_file_path)
                        except Exception as e:
                            print(f"Error deleting temp file {temp_file_path}: {e}")
            else:
                await message_or_query.bot.send_message(
                    chat_id=message_or_query.from_user.id,
                    text=text
                )
        else:
            await message_or_query.bot.send_message(
                chat_id=message_or_query.from_user.id,
                text=text
            )
    else:
        await message_or_query.bot.send_message(
            chat_id=message_or_query.from_user.id,
            text=text
        )

    await message_or_query.bot.send_message(
        chat_id=message_or_query.from_user.id,
        text="Publish post?",
        reply_markup=yes_no_keyboard("publish")
    )
    await state.set_state(GeneratePostStates.wait_for_publish_confirmation)


@generate_post_handler.callback_query(GeneratePostStates.wait_for_publish_confirmation, F.data.in_(["publish_yes", "publish_no"]))
async def handle_publish_decision(query: CallbackQuery, state: FSMContext):
    if query.data == "publish_yes":
        data = await state.get_data()
        include_photos = data.get("include_photos", False)
        comment = data.get("comment", "")
        generator = data["generator"]

        text = generator.generate_text(comment)

        if include_photos:
            images_urls = generator.get_first_three_images()
            if images_urls:
                media = []
                for i, url in enumerate(images_urls[:3]):
                    if i == 0:
                        media.append(InputMediaPhoto(media=url, caption=text))
                    else:
                        media.append(InputMediaPhoto(media=url))
                await query.bot.send_media_group(
                    chat_id=CHANNEL_ID,
                    media=media
                )
            else:
                await query.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=text
                )
        else:
            await query.bot.send_message(
                chat_id=CHANNEL_ID,
                text=text
            )
        await query.message.edit_text("Post published successfully!")
    else:
        await query.message.edit_text("Post publication canceled.")
    await state.clear()
    await query.answer()

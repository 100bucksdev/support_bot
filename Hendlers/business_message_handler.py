from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import BusinessConnection, Message, FSInputFile, CallbackQuery

from bot import bot
from external_service import make_request
from process_new_business_message import process_new_business_message

business_message_handler = Router()

@business_message_handler.business_connection()
async def handle_business_connection(connection: BusinessConnection):
    if connection.is_enabled:
        rights = connection.rights
        required_keys = ['can_reply', 'can_read_messages']
        if not all(rights.get(key) is True for key in required_keys):
            image = FSInputFile("src/image/rights_image.jpg")
            await bot.send_photo(photo=image, chat_id=connection.user.id, caption="You must enable these permits so that the bot works normally")
            return

        response = await make_request(url=f'account/user/{connection.user.id}')
        data = {'user_id': connection.user.id, 'is_active': True, 'connection_id': connection.id,
                'username': connection.user.username}
        if response['status'] == 200:

            response = await make_request(url=f'account/user/{connection.user.id}', method='PUT', data=data)
            if response['status'] == 200:
                await bot.send_message(connection.user.id, "You are connected to the bot")
        else:
            response = await make_request(url=f'account', method='POST', data=data)
            if response['status'] == 200:
                await bot.send_message(connection.user.id, "You are connected to the bot")
    else:
        response = await make_request(url=f'account/user/{connection.user.id}/active', method='PUT', data={'is_active': False})
        if response['status'] == 200:
            await bot.send_message(connection.user.id, "You are disconnected your account from the bot")

@business_message_handler.business_message()
async def handle_business_message(message: Message):
    await process_new_business_message(message)


@business_message_handler.callback_query(F.data.startswith('send_answer_'))
async def send_answer_handler(query: CallbackQuery):
    ai_response_id = query.data.split('_')[-3]
    chat_with_client_id = query.data.split('_')[-2]
    business_connection_id = query.data.split('_')[-1]

    response = await make_request(url=f'ai-response/{ai_response_id}')
    if response['status'] != 200:
        await query.answer("❌ Error sending answer. Please try again later")
        return
    data = response['body']
    answer = data.get('ai_response')
    message = await bot.send_message(chat_id=chat_with_client_id, text=answer, business_connection_id=business_connection_id)
    await query.answer()
    await query.message.edit_text('✅ Successfully sent answer')
    data = {
        "message": answer,
        "sender": "ai",
        "chat_with_user_id": message.chat.id,
        "message_id": message.message_id
    }
    message_response = await make_request(url=f'account/user/{query.from_user.id}/chat/{message.chat.id}/message',
                                              method='POST',
                                              data=data)

    if message_response.get("status") != 200:
        return
    else:
        answer_message_id = message_response.get("body").get("id")

    await make_request(url=f'ai-response/{ai_response_id}', method='PUT', data={'answer_message_id': answer_message_id})






@business_message_handler.message(Command("connect"))
async def handle_message(message: Message):
    user_id = message.from_user.id

    response = await make_request(url=f'account/user/{user_id}')
    if response['status'] not in [200, 404]:
        await message.answer("Error connecting with server. Please try again later")
    data = response['body']


    if data.get('is_active') is True:
        await message.answer("You are already connected your account to the bot")
        return
    if not message.from_user.is_premium:
        await message.answer("You don't have telegram premium. You need to subscribe to connect the bot to your account")
        return

    video = FSInputFile("src/video/info_video.mp4")
    await message.reply_video(video, caption="Here is the instruction how to connect this bot to your account")


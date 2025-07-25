
import asyncio

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from Hendlers.add_new_patterns import new_pattern_router
from Hendlers.business_message_handler import business_message_handler
from Hendlers.generate_post_handler import generate_post_handler
from Hendlers.in_chat_handler import in_chat_handler
from Hendlers.inline_keyboard_handler import inline_handler
from Hendlers.markup_keyboard_handler import markup_handler
from Hendlers.start import start
from bot import bot


async def main():
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)


    dp.include_router(business_message_handler)
    dp.include_router(new_pattern_router)

    dp.include_router(generate_post_handler)

    dp.include_router(start)



    dp.include_router(markup_handler)
    dp.include_router(inline_handler)
    dp.include_router(in_chat_handler)




    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    print('project starts')
    asyncio.run(main())
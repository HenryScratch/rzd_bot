import asyncio
import logging
import sys

import motor.motor_asyncio
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bson import ObjectId

from routes import router

# from os import getenv


# TOKEN = getenv("BOT_TOKEN")

TOKEN = os.getenv('BOT_TOKEN', "7243990999:AAFClmjRHzc2ByuG-UvxALB54urEfp4UAvk")

dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

client = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
db_queue = client.queue


async def process_queue():
    while True:
        # Получение и удаление первого элемента из очереди (FIFO)
        user = await db_queue.work.find_one_and_delete({})

        if user:
            # user_id = user['user_id']
            try:
                # Отправка сообщения пользователю
                await bot.send_message(
                    user["user_id"], f"Изменения в маршруте {user['number_route']}"
                )
            except Exception as e:
                print(f"Failed to send message to user {user['user_id']}: {e}")

        # Задержка перед следующей проверкой очереди
        await asyncio.sleep(5)  # Проверяет очередь каждые 5 секунд


async def on_startup():
    """Запускает обработчик очереди при старте бота."""
    asyncio.create_task(process_queue())


async def main() -> None:
    # bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(router)

    await on_startup()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

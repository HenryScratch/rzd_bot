import asyncio
import logging
import os
import sys

import motor.motor_asyncio
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bson import ObjectId

from routes import router

TOKEN = os.getenv("BOT_TOKEN", "8089418834:AAG6thF_y2Ipaw1_TC8uG55_ea_Ib8ABs88")


dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
# print(os.getenv("MONGO_URL", "mongodb://mongo:27017"))
client = motor.motor_asyncio.AsyncIOMotorClient(
    os.getenv("MONGO_URL", "mongodb://mongo:27017")
)
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
                await bot.send_message(
                    7507888182,
                    f"Изменения в маршруте {user['number_route']}, userid={user['user_id']}",
                )

            except Exception as e:
                print(f"Failed to send message to user {user['user_id']}: {e}")

        # Задержка перед следующей проверкой очереди
        await asyncio.sleep(2)  # Проверяет очередь каждые 5 секунд


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
